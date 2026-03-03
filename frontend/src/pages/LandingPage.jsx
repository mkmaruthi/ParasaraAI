import { useNavigate } from 'react-router-dom';
import { Sparkles, Moon, Star, ArrowRight, Scroll } from 'lucide-react';
import { Button } from '@/components/ui/button';

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero Section */}
      <main className="flex-1 flex flex-direction-col items-center justify-center px-4 py-12">
        <div className="text-center max-w-4xl mx-auto">
          {/* Logo/Brand */}
          <div className="flex items-center justify-center gap-3 mb-6 animate-fade-in">
            <Moon className="w-10 h-10 text-cosmic-brand-accent" />
            <Sparkles className="w-6 h-6 text-cosmic-text-secondary" />
            <Star className="w-8 h-8 text-cosmic-brand-primary" />
          </div>
          
          {/* Title */}
          <h1 
            className="font-cinzel text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-4 tracking-wide"
            style={{ textShadow: '0 0 30px rgba(124, 58, 237, 0.5)' }}
            data-testid="landing-title"
          >
            Parasara Astro AI
          </h1>
          
          {/* Tagline */}
          <p className="font-inter text-lg md:text-xl text-cosmic-text-secondary mb-8 max-w-2xl mx-auto leading-relaxed">
            Discover Your Cosmic Blueprint Through Ancient Vedic Wisdom
          </p>
          
          {/* Subtext */}
          <p className="text-cosmic-text-muted text-base mb-12 max-w-xl mx-auto">
            Powered by precise astronomical calculations and intelligent interpretation. 
            Get your authentic South Indian birth chart with personalized insights.
          </p>
          
          {/* CTA Button */}
          <Button
            onClick={() => navigate('/create')}
            className="star-button text-lg px-8 py-6 h-auto"
            data-testid="get-started-btn"
          >
            <span className="flex items-center gap-3">
              Begin Your Journey
              <ArrowRight className="w-5 h-5" />
            </span>
          </Button>
          
          {/* Features Grid */}
          <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6">
            <FeatureCard
              icon={<Scroll className="w-8 h-8" />}
              title="Authentic Charts"
              description="Traditional South Indian style birth charts computed with astronomical precision"
            />
            <FeatureCard
              icon={<Sparkles className="w-8 h-8" />}
              title="AI Interpretation"
              description="Intelligent analysis of your chart data by a knowledgeable astrology assistant"
            />
            <FeatureCard
              icon={<Moon className="w-8 h-8" />}
              title="Interactive Chat"
              description="Ask follow-up questions and explore your chart with conversational guidance"
            />
          </div>
        </div>
      </main>
      
      {/* Footer */}
      <footer className="py-6 text-center text-cosmic-text-muted text-sm border-t border-white/5">
        <p>Parasara Astro AI • Vedic Astrology with Modern Intelligence</p>
      </footer>
    </div>
  );
};

const FeatureCard = ({ icon, title, description }) => (
  <div 
    className="glass-card p-6 text-center"
    data-testid={`feature-${title.toLowerCase().replace(/\s+/g, '-')}`}
  >
    <div className="text-cosmic-brand-accent mb-4 flex justify-center">
      {icon}
    </div>
    <h3 className="font-cinzel text-lg text-white mb-2">{title}</h3>
    <p className="text-cosmic-text-muted text-sm">{description}</p>
  </div>
);

export default LandingPage;
