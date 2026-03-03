import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, Send, History, Plus, Trash2, Loader2, 
  Sun, Moon, Star, ChevronDown, ChevronUp, Menu, X 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Collapsible, 
  CollapsibleContent, 
  CollapsibleTrigger 
} from '@/components/ui/collapsible';
import { toast } from 'sonner';
import axios from 'axios';
import SouthIndianChart from '@/components/SouthIndianChart';

const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ResultsPage = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const chatEndRef = useRef(null);
  
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dashaOpen, setDashaOpen] = useState(false);
  const [planetsOpen, setPlanetsOpen] = useState(true);

  // Load session data
  useEffect(() => {
    loadSession();
    loadSessions();
  }, [sessionId]);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadSession = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/chart/session/${sessionId}`);
      setSession(response.data.session);
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error('Failed to load session:', error);
      toast.error('Failed to load chart session');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const loadSessions = async () => {
    try {
      const response = await axios.get(`${API_URL}/chart/sessions`);
      setSessions(response.data.sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || sending) return;

    const userMessage = chatInput.trim();
    setChatInput('');
    setSending(true);

    // Optimistic update
    const tempUserMsg = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const response = await axios.post(`${API_URL}/chat`, {
        session_id: sessionId,
        message: userMessage,
      });

      // Add assistant response
      const assistantMsg = {
        id: response.data.message_id,
        role: 'assistant',
        content: response.data.response,
        timestamp: response.data.timestamp,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error) {
      console.error('Chat error:', error);
      toast.error('Failed to send message');
      // Remove optimistic message on error
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id));
    } finally {
      setSending(false);
    }
  };

  const deleteSession = async (id) => {
    if (!window.confirm('Delete this chart session?')) return;
    
    try {
      await axios.delete(`${API_URL}/chart/session/${id}`);
      toast.success('Session deleted');
      if (id === sessionId) {
        navigate('/create');
      } else {
        loadSessions();
      }
    } catch (error) {
      toast.error('Failed to delete session');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="cosmic-spinner mx-auto mb-4" />
          <p className="text-cosmic-text-secondary">Loading your chart...</p>
        </div>
      </div>
    );
  }

  const chartData = session?.chart_data || {};
  const birthInfo = session?.birth_details || {};
  const prediction = session?.chart_data?.raw_data?.prediction || '';

  return (
    <div className="min-h-screen flex">
      {/* Mobile Sidebar Toggle */}
      <Button
        variant="ghost"
        className="fixed top-4 left-4 z-50 md:hidden"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        data-testid="sidebar-toggle"
      >
        {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </Button>

      {/* Sidebar */}
      <aside 
        className={`fixed md:static inset-y-0 left-0 z-40 w-72 history-sidebar transform transition-transform duration-300 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
        data-testid="history-sidebar"
      >
        <div className="p-4 border-b border-white/10">
          <Button
            onClick={() => navigate('/create')}
            className="w-full bg-cosmic-brand-secondary hover:bg-cosmic-brand-primary"
            data-testid="new-chart-btn"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Chart
          </Button>
        </div>
        
        <div className="p-4">
          <h3 className="font-cinzel text-cosmic-text-secondary text-sm mb-3 flex items-center gap-2">
            <History className="w-4 h-4" />
            Chart History
          </h3>
          
          <ScrollArea className="h-[calc(100vh-180px)]">
            {sessions.length === 0 ? (
              <p className="text-cosmic-text-muted text-sm">No previous charts</p>
            ) : (
              sessions.map((s) => (
                <div
                  key={s.id}
                  className={`history-item group ${s.id === sessionId ? 'active' : ''}`}
                  onClick={() => {
                    navigate(`/results/${s.id}`);
                    setSidebarOpen(false);
                  }}
                  data-testid={`history-item-${s.id}`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-sm truncate">{s.name}</p>
                      <p className="text-cosmic-text-muted text-xs">
                        {new Date(s.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="opacity-0 group-hover:opacity-100 h-6 w-6"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteSession(s.id);
                      }}
                      data-testid={`delete-session-${s.id}`}
                    >
                      <Trash2 className="w-3 h-3 text-red-400" />
                    </Button>
                  </div>
                </div>
              ))
            )}
          </ScrollArea>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-h-screen md:ml-0">
        {/* Header */}
        <header className="p-4 border-b border-white/10 flex items-center gap-4">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="text-cosmic-text-secondary hover:text-white"
            data-testid="home-btn"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Home
          </Button>
          <h1 className="font-cinzel text-xl text-white truncate">
            {session?.name}'s Chart
          </h1>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-4 md:p-6">
          <Tabs defaultValue="chart" className="w-full">
            <TabsList className="mb-6 bg-cosmic-bg-secondary">
              <TabsTrigger value="chart" data-testid="tab-chart">Chart</TabsTrigger>
              <TabsTrigger value="prediction" data-testid="tab-prediction">Prediction</TabsTrigger>
              <TabsTrigger value="chat" data-testid="tab-chat">Chat</TabsTrigger>
            </TabsList>

            {/* Chart Tab */}
            <TabsContent value="chart" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Chart */}
                <div className="glass-card p-4 md:p-6">
                  <h2 className="font-cinzel text-cosmic-brand-accent text-lg mb-4">
                    Birth Chart (D1 - Rasi)
                  </h2>
                  <SouthIndianChart chartData={chartData} birthInfo={birthInfo} />
                </div>

                {/* Chart Details */}
                <div className="space-y-4">
                  {/* Birth Info */}
                  <div className="glass-card p-4">
                    <h3 className="font-cinzel text-cosmic-brand-accent text-sm mb-3">Birth Details</h3>
                    <div className="space-y-2 text-sm">
                      <DataRow label="Name" value={birthInfo.name} />
                      <DataRow label="Date" value={birthInfo.date_of_birth} />
                      <DataRow label="Time" value={birthInfo.time_of_birth} />
                      <DataRow label="Place" value={birthInfo.place_of_birth} />
                      <DataRow 
                        label="Coordinates" 
                        value={`${birthInfo.latitude?.toFixed(4)}°, ${birthInfo.longitude?.toFixed(4)}°`} 
                      />
                      <DataRow label="Timezone" value={birthInfo.timezone} />
                    </div>
                  </div>

                  {/* Key Chart Facts */}
                  <div className="glass-card p-4">
                    <h3 className="font-cinzel text-cosmic-brand-accent text-sm mb-3">Key Chart Facts</h3>
                    <div className="space-y-2 text-sm">
                      <DataRow 
                        label="Lagna (Ascendant)" 
                        value={`${chartData.ascendant?.sign || 'N/A'} ${chartData.ascendant?.degree ? `(${chartData.ascendant.degree}°)` : ''}`}
                        icon={<Sun className="w-4 h-4 text-yellow-400" />}
                      />
                      <DataRow 
                        label="Rasi (Moon Sign)" 
                        value={chartData.nakshatra?.moon_sign || 'N/A'}
                        icon={<Moon className="w-4 h-4 text-blue-300" />}
                      />
                      <DataRow 
                        label="Nakshatra" 
                        value={`${chartData.nakshatra?.nakshatra || 'N/A'} ${chartData.nakshatra?.pada ? `(Pada ${chartData.nakshatra.pada})` : ''}`}
                        icon={<Star className="w-4 h-4 text-purple-300" />}
                      />
                    </div>
                  </div>

                  {/* Planetary Positions */}
                  <Collapsible open={planetsOpen} onOpenChange={setPlanetsOpen}>
                    <div className="glass-card p-4">
                      <CollapsibleTrigger className="w-full flex justify-between items-center" data-testid="planets-toggle">
                        <h3 className="font-cinzel text-cosmic-brand-accent text-sm">Planetary Positions</h3>
                        {planetsOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <div className="mt-3 space-y-1 text-xs">
                          <div className="grid grid-cols-5 gap-2 text-cosmic-text-muted border-b border-white/10 pb-2 mb-2">
                            <span>Planet</span>
                            <span>Sign</span>
                            <span>House</span>
                            <span>Degree</span>
                            <span>Nakshatra</span>
                          </div>
                          {chartData.planets?.filter(p => p.name !== 'Ascendant').map((planet, idx) => (
                            <div 
                              key={idx} 
                              className="grid grid-cols-5 gap-2 text-cosmic-text-secondary py-1"
                              data-testid={`planet-row-${planet.name?.toLowerCase()}`}
                            >
                              <span className={planet.retrograde ? 'text-red-400' : ''}>
                                {planet.name} {planet.retrograde ? '(R)' : ''}
                              </span>
                              <span>{planet.sign}</span>
                              <span>{planet.house}</span>
                              <span className="font-mono">{planet.degree}°</span>
                              <span className="truncate">{planet.nakshatra}</span>
                            </div>
                          ))}
                        </div>
                      </CollapsibleContent>
                    </div>
                  </Collapsible>

                  {/* Dasha Information */}
                  {chartData.dasha && (
                    <Collapsible open={dashaOpen} onOpenChange={setDashaOpen}>
                      <div className="glass-card p-4">
                        <CollapsibleTrigger className="w-full flex justify-between items-center" data-testid="dasha-toggle">
                          <h3 className="font-cinzel text-cosmic-brand-accent text-sm">Vimshottari Dasha</h3>
                          {dashaOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </CollapsibleTrigger>
                        <CollapsibleContent>
                          <div className="mt-3 space-y-2 text-sm">
                            {chartData.dasha.current_dasha && (
                              <DataRow label="Current Dasha" value={chartData.dasha.current_dasha} />
                            )}
                            {chartData.dasha.dasha_balance && (
                              <DataRow label="Dasha Balance" value={chartData.dasha.dasha_balance} />
                            )}
                            {chartData.dasha.maha_dasha && typeof chartData.dasha.maha_dasha === 'object' && (
                              <div className="mt-2">
                                <p className="text-cosmic-text-muted text-xs mb-1">Maha Dasha Periods:</p>
                                {Object.entries(chartData.dasha.maha_dasha).slice(0, 5).map(([planet, info]) => (
                                  <div key={planet} className="text-xs text-cosmic-text-secondary py-0.5">
                                    {planet}: {typeof info === 'object' ? JSON.stringify(info) : info}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </CollapsibleContent>
                      </div>
                    </Collapsible>
                  )}
                </div>
              </div>
            </TabsContent>

            {/* Prediction Tab */}
            <TabsContent value="prediction">
              <div className="glass-card p-6 max-w-5xl mx-auto overflow-auto max-h-[calc(100vh-250px)]">
                <h2 className="font-cinzel text-cosmic-brand-accent text-xl mb-6">
                  Detailed Vedic Astrology Report (BPHS)
                </h2>
                <div className="prediction-content prose prose-invert max-w-none" data-testid="prediction-content">
                  {session?.chart_data?.prediction ? (
                    <PredictionRenderer content={session.chart_data.prediction} />
                  ) : session?.chart_data?.raw_data?.prediction ? (
                    <PredictionRenderer content={session.chart_data.raw_data.prediction} />
                  ) : (
                    <div className="text-center py-12">
                      <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-cosmic-brand-accent" />
                      <p className="text-cosmic-text-muted">Generating detailed BPHS analysis...</p>
                      <p className="text-cosmic-text-muted text-sm mt-2">This may take a moment</p>
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>

            {/* Chat Tab */}
            <TabsContent value="chat" className="h-[calc(100vh-300px)]">
              <div className="glass-card h-full flex flex-col">
                {/* Chat Messages */}
                <ScrollArea className="flex-1 p-4" data-testid="chat-messages">
                  {messages.length === 0 ? (
                    <div className="text-center py-12">
                      <p className="text-cosmic-text-muted mb-4">
                        Ask questions about your chart
                      </p>
                      <div className="space-y-2">
                        {[
                          "What does my Moon sign mean?",
                          "How is my career outlook based on the chart?",
                          "Explain my current Dasha period",
                          "What are the effects of retrograde planets?"
                        ].map((q, i) => (
                          <button
                            key={i}
                            onClick={() => setChatInput(q)}
                            className="block w-full max-w-md mx-auto text-left p-3 text-sm bg-cosmic-brand-secondary/20 hover:bg-cosmic-brand-secondary/40 rounded-lg text-cosmic-text-secondary transition-colors"
                            data-testid={`suggested-question-${i}`}
                          >
                            {q}
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {messages.map((msg) => (
                        <div
                          key={msg.id}
                          className={`chat-bubble ${msg.role}`}
                          data-testid={`chat-message-${msg.role}`}
                        >
                          <p className="whitespace-pre-wrap">{msg.content}</p>
                          <span className="text-xs opacity-50 mt-2 block">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                      ))}
                      {sending && (
                        <div className="chat-bubble assistant">
                          <Loader2 className="w-4 h-4 animate-spin" />
                        </div>
                      )}
                      <div ref={chatEndRef} />
                    </div>
                  )}
                </ScrollArea>

                {/* Chat Input */}
                <form onSubmit={sendMessage} className="chat-input-area flex gap-2">
                  <Input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask about your chart..."
                    className="flex-1 bg-transparent border-white/20 text-white placeholder:text-white/40"
                    disabled={sending}
                    data-testid="chat-input"
                  />
                  <Button
                    type="submit"
                    disabled={sending || !chatInput.trim()}
                    className="bg-cosmic-brand-primary hover:bg-cosmic-brand-secondary"
                    data-testid="send-message-btn"
                  >
                    {sending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </Button>
                </form>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
};

// Helper Components
const DataRow = ({ label, value, icon }) => (
  <div className="data-row flex justify-between items-center">
    <span className="data-label flex items-center gap-2">
      {icon}
      {label}
    </span>
    <span className="data-value">{value || 'N/A'}</span>
  </div>
);

const PredictionRenderer = ({ content }) => {
  // Use dynamic import for react-markdown
  const [ReactMarkdown, setReactMarkdown] = useState(null);
  const [remarkGfm, setRemarkGfm] = useState(null);
  
  useEffect(() => {
    // Dynamically import markdown libraries
    Promise.all([
      import('react-markdown'),
      import('remark-gfm')
    ]).then(([md, gfm]) => {
      setReactMarkdown(() => md.default);
      setRemarkGfm(() => gfm.default);
    });
  }, []);
  
  if (!ReactMarkdown || !remarkGfm) {
    // Fallback to simple rendering while loading
    return (
      <div className="space-y-4">
        {content.split('\n').map((line, idx) => {
          if (line.startsWith('## ')) {
            return <h2 key={idx} className="font-cinzel text-cosmic-brand-accent text-lg mt-6 border-b border-cosmic-brand-accent/30 pb-2">{line.replace('## ', '')}</h2>;
          }
          if (line.startsWith('### ')) {
            return <h3 key={idx} className="font-cinzel text-cosmic-brand-accent mt-4">{line.replace('### ', '')}</h3>;
          }
          if (line.startsWith('|')) {
            return <code key={idx} className="block text-xs text-cosmic-text-secondary font-mono">{line}</code>;
          }
          if (line.trim() === '') return <br key={idx} />;
          return <p key={idx} className="text-cosmic-text-secondary leading-relaxed">{line}</p>;
        })}
      </div>
    );
  }
  
  return (
    <div className="markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({children}) => <h1 className="font-cinzel text-cosmic-brand-accent text-2xl mt-8 mb-4 border-b border-cosmic-brand-accent/30 pb-2">{children}</h1>,
          h2: ({children}) => <h2 className="font-cinzel text-cosmic-brand-accent text-xl mt-8 mb-4 border-b border-cosmic-brand-accent/30 pb-2">{children}</h2>,
          h3: ({children}) => <h3 className="font-cinzel text-cosmic-brand-accent text-lg mt-6 mb-3">{children}</h3>,
          h4: ({children}) => <h4 className="font-cinzel text-cosmic-text-primary text-base mt-4 mb-2">{children}</h4>,
          p: ({children}) => <p className="text-cosmic-text-secondary leading-relaxed mb-4">{children}</p>,
          ul: ({children}) => <ul className="list-disc list-inside space-y-1 mb-4 text-cosmic-text-secondary">{children}</ul>,
          ol: ({children}) => <ol className="list-decimal list-inside space-y-1 mb-4 text-cosmic-text-secondary">{children}</ol>,
          li: ({children}) => <li className="text-cosmic-text-secondary ml-2">{children}</li>,
          strong: ({children}) => <strong className="text-cosmic-brand-accent font-semibold">{children}</strong>,
          em: ({children}) => <em className="text-cosmic-text-primary italic">{children}</em>,
          table: ({children}) => (
            <div className="overflow-x-auto my-4">
              <table className="w-full border-collapse border border-cosmic-brand-accent/30 text-sm">
                {children}
              </table>
            </div>
          ),
          thead: ({children}) => <thead className="bg-cosmic-brand-secondary/30">{children}</thead>,
          tbody: ({children}) => <tbody>{children}</tbody>,
          tr: ({children}) => <tr className="border-b border-cosmic-brand-accent/20">{children}</tr>,
          th: ({children}) => <th className="px-3 py-2 text-left text-cosmic-brand-accent font-cinzel text-xs uppercase">{children}</th>,
          td: ({children}) => <td className="px-3 py-2 text-cosmic-text-secondary">{children}</td>,
          blockquote: ({children}) => (
            <blockquote className="border-l-4 border-cosmic-brand-accent pl-4 italic text-cosmic-text-muted my-4">
              {children}
            </blockquote>
          ),
          code: ({children, inline}) => 
            inline ? (
              <code className="bg-cosmic-bg-secondary px-1 py-0.5 rounded text-cosmic-text-primary text-sm">{children}</code>
            ) : (
              <pre className="bg-cosmic-bg-secondary p-4 rounded-lg overflow-x-auto my-4">
                <code className="text-cosmic-text-secondary text-sm">{children}</code>
              </pre>
            ),
          hr: () => <hr className="my-6 border-cosmic-brand-accent/30" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default ResultsPage;
