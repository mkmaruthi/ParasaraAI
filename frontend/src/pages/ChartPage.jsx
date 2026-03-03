import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, MapPin, Calendar, Clock, User, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Debounce hook for auto-suggest
const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
};

const ChartPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [placeLoading, setPlaceLoading] = useState(false);
  const [placeResults, setPlaceResults] = useState([]);
  const [selectedPlace, setSelectedPlace] = useState(null);
  const [showManualCoords, setShowManualCoords] = useState(false);
  const [placeQuery, setPlaceQuery] = useState('');
  const placeInputRef = useRef(null);
  
  const [formData, setFormData] = useState({
    name: '',
    dateOfBirth: '',
    timeOfBirth: '',
    placeOfBirth: '',
    gender: 'unknown',
    latitude: '',
    longitude: '',
    timezone: '',
  });

  // Debounce the place query for auto-suggest
  const debouncedPlaceQuery = useDebounce(placeQuery, 400);

  // Auto-search when user types (debounced)
  useEffect(() => {
    if (debouncedPlaceQuery && debouncedPlaceQuery.length >= 3 && !selectedPlace) {
      searchPlace(debouncedPlaceQuery);
    } else if (debouncedPlaceQuery.length < 3) {
      setPlaceResults([]);
    }
  }, [debouncedPlaceQuery]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handlePlaceInputChange = (e) => {
    const value = e.target.value;
    setPlaceQuery(value);
    setFormData((prev) => ({ ...prev, placeOfBirth: value }));
    // Clear selected place when user starts typing again
    if (selectedPlace) {
      setSelectedPlace(null);
      setFormData((prev) => ({ ...prev, latitude: '', longitude: '', timezone: '' }));
    }
  };

  const searchPlace = async (query) => {
    if (!query || query.length < 3) return;
    
    setPlaceLoading(true);
    try {
      const response = await axios.post(`${API_URL}/geocode?place_name=${encodeURIComponent(query)}`);
      const results = response.data.results || [];
      setPlaceResults(results);
      
      if (results.length === 0 && query.length > 5) {
        // Only show manual option if query is substantial
        setShowManualCoords(true);
      }
    } catch (error) {
      console.error('Place search error:', error);
      if (query.length > 5) {
        setShowManualCoords(true);
      }
    } finally {
      setPlaceLoading(false);
    }
  };

  const selectPlace = (place) => {
    setSelectedPlace(place);
    setFormData((prev) => ({
      ...prev,
      placeOfBirth: place.formatted_address,
      latitude: place.latitude,
      longitude: place.longitude,
      timezone: place.timezone,
    }));
    setPlaceResults([]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.name.trim()) {
      toast.error('Please enter your name');
      return;
    }
    if (!formData.dateOfBirth) {
      toast.error('Please enter your date of birth');
      return;
    }
    if (!formData.timeOfBirth) {
      toast.error('Please enter your time of birth');
      return;
    }
    if (!formData.placeOfBirth && !formData.latitude) {
      toast.error('Please enter your place of birth or coordinates');
      return;
    }
    
    setLoading(true);
    
    try {
      const payload = {
        name: formData.name.trim(),
        date_of_birth: formData.dateOfBirth,
        time_of_birth: formData.timeOfBirth,
        place_of_birth: formData.placeOfBirth || 'Manual Entry',
        gender: formData.gender,
        latitude: formData.latitude ? parseFloat(formData.latitude) : null,
        longitude: formData.longitude ? parseFloat(formData.longitude) : null,
        timezone_str: formData.timezone || null,
      };
      
      toast.info('Calculating your birth chart... This may take a moment.');
      
      const response = await axios.post(`${API_URL}/chart/generate`, payload);
      
      if (response.data.session_id) {
        toast.success('Chart generated successfully!');
        navigate(`/results/${response.data.session_id}`);
      }
    } catch (error) {
      console.error('Chart generation error:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to generate chart. Please check your inputs.';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="text-cosmic-text-secondary hover:text-white mb-4"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <h1 className="font-cinzel text-3xl md:text-4xl text-white mb-2" data-testid="create-chart-title">
            Create Your Birth Chart
          </h1>
          <p className="text-cosmic-text-muted">
            Enter your birth details below for an accurate Vedic astrology reading
          </p>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="glass-card p-6 md:p-8 space-y-6">
          {/* Name */}
          <div className="space-y-2">
            <Label htmlFor="name" className="text-cosmic-text-secondary flex items-center gap-2">
              <User className="w-4 h-4" />
              Full Name
            </Label>
            <Input
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="Enter your full name"
              className="bg-transparent border-b border-white/20 rounded-none focus:border-cosmic-brand-accent focus:ring-0 text-white placeholder:text-white/40"
              data-testid="name-input"
            />
          </div>
          
          {/* Date of Birth */}
          <div className="space-y-2">
            <Label htmlFor="dateOfBirth" className="text-cosmic-text-secondary flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Date of Birth
            </Label>
            <Input
              id="dateOfBirth"
              name="dateOfBirth"
              type="date"
              value={formData.dateOfBirth}
              onChange={handleInputChange}
              className="bg-transparent border-b border-white/20 rounded-none focus:border-cosmic-brand-accent focus:ring-0 text-white [color-scheme:dark]"
              data-testid="dob-input"
            />
          </div>
          
          {/* Time of Birth */}
          <div className="space-y-2">
            <Label htmlFor="timeOfBirth" className="text-cosmic-text-secondary flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Time of Birth (24-hour format)
            </Label>
            <div className="flex items-center gap-2">
              <Input
                id="timeOfBirth"
                name="timeOfBirth"
                type="time"
                step="1"
                value={formData.timeOfBirth}
                onChange={handleInputChange}
                className="flex-1 bg-transparent border-b border-white/20 rounded-none focus:border-cosmic-brand-accent focus:ring-0 text-white [color-scheme:dark]"
                data-testid="time-input"
              />
              <span className="text-cosmic-text-muted text-sm whitespace-nowrap">
                {formData.timeOfBirth ? `(${formData.timeOfBirth})` : '(HH:MM:SS)'}
              </span>
            </div>
            <p className="text-xs text-cosmic-text-muted">Enter time in 24-hour format (e.g., 14:30 for 2:30 PM). Seconds optional.</p>
          </div>
          
          {/* Place of Birth */}
          <div className="space-y-2 relative">
            <Label htmlFor="placeOfBirth" className="text-cosmic-text-secondary flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              Place of Birth
            </Label>
            <div className="relative">
              <Input
                ref={placeInputRef}
                id="placeOfBirth"
                name="placeOfBirth"
                value={formData.placeOfBirth}
                onChange={handlePlaceInputChange}
                placeholder="Start typing city name..."
                autoComplete="off"
                className="w-full bg-transparent border-b border-white/20 rounded-none focus:border-cosmic-brand-accent focus:ring-0 text-white placeholder:text-white/40"
                data-testid="place-input"
              />
              {placeLoading && (
                <div className="absolute right-2 top-1/2 -translate-y-1/2">
                  <Loader2 className="w-4 h-4 animate-spin text-cosmic-brand-accent" />
                </div>
              )}
            </div>
            
            {/* Place Results - Auto-suggest dropdown */}
            {placeResults.length > 0 && !selectedPlace && (
              <div 
                className="absolute z-50 w-full mt-1 bg-cosmic-bg-secondary/95 backdrop-blur-md rounded-lg border border-white/10 shadow-xl overflow-hidden" 
                data-testid="place-results"
              >
                <p className="text-xs text-cosmic-text-muted px-3 py-2 border-b border-white/5">
                  Select your birthplace:
                </p>
                <div className="max-h-60 overflow-y-auto">
                  {placeResults.map((place, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => selectPlace(place)}
                      className="w-full text-left px-3 py-2.5 hover:bg-cosmic-brand-primary/30 text-sm text-white transition-colors border-b border-white/5 last:border-0"
                      data-testid={`place-option-${index}`}
                    >
                      <span className="flex items-center gap-2">
                        <MapPin className="w-3 h-3 text-cosmic-brand-accent flex-shrink-0" />
                        <span className="truncate">{place.formatted_address}</span>
                      </span>
                      <span className="text-xs text-cosmic-text-muted ml-5 block mt-0.5">
                        {place.latitude.toFixed(4)}°, {place.longitude.toFixed(4)}° • {place.timezone}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Selected Place Info */}
            {selectedPlace && (
              <div className="mt-2 p-3 bg-cosmic-brand-secondary/20 rounded-lg" data-testid="selected-place">
                <p className="text-sm text-cosmic-text-secondary">Selected Location:</p>
                <p className="text-white">{selectedPlace.formatted_address}</p>
                <p className="text-xs text-cosmic-text-muted">
                  Coordinates: {selectedPlace.latitude.toFixed(4)}°, {selectedPlace.longitude.toFixed(4)}° | 
                  Timezone: {selectedPlace.timezone}
                </p>
              </div>
            )}
            
            {/* Manual Coordinates Toggle */}
            <button
              type="button"
              onClick={() => setShowManualCoords(!showManualCoords)}
              className="text-xs text-cosmic-brand-accent hover:underline mt-2"
              data-testid="manual-coords-toggle"
            >
              {showManualCoords ? 'Hide manual entry' : 'Enter coordinates manually'}
            </button>
          </div>
          
          {/* Manual Coordinates */}
          {showManualCoords && (
            <div className="grid grid-cols-3 gap-4 p-4 bg-black/30 rounded-lg" data-testid="manual-coords-section">
              <div className="space-y-2">
                <Label htmlFor="latitude" className="text-cosmic-text-secondary text-xs">
                  Latitude
                </Label>
                <Input
                  id="latitude"
                  name="latitude"
                  type="number"
                  step="0.0001"
                  value={formData.latitude}
                  onChange={handleInputChange}
                  placeholder="e.g., 28.6139"
                  className="bg-transparent border-b border-white/20 rounded-none focus:border-cosmic-brand-accent focus:ring-0 text-white text-sm"
                  data-testid="latitude-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="longitude" className="text-cosmic-text-secondary text-xs">
                  Longitude
                </Label>
                <Input
                  id="longitude"
                  name="longitude"
                  type="number"
                  step="0.0001"
                  value={formData.longitude}
                  onChange={handleInputChange}
                  placeholder="e.g., 77.2090"
                  className="bg-transparent border-b border-white/20 rounded-none focus:border-cosmic-brand-accent focus:ring-0 text-white text-sm"
                  data-testid="longitude-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="timezone" className="text-cosmic-text-secondary text-xs">
                  Timezone
                </Label>
                <Input
                  id="timezone"
                  name="timezone"
                  value={formData.timezone}
                  onChange={handleInputChange}
                  placeholder="e.g., Asia/Kolkata"
                  className="bg-transparent border-b border-white/20 rounded-none focus:border-cosmic-brand-accent focus:ring-0 text-white text-sm"
                  data-testid="timezone-input"
                />
              </div>
            </div>
          )}
          
          {/* Gender (Optional) */}
          <div className="space-y-2">
            <Label htmlFor="gender" className="text-cosmic-text-secondary">
              Gender (Optional)
            </Label>
            <Select
              value={formData.gender}
              onValueChange={(value) => setFormData((prev) => ({ ...prev, gender: value }))}
            >
              <SelectTrigger 
                className="bg-transparent border-b border-white/20 rounded-none focus:border-cosmic-brand-accent text-white"
                data-testid="gender-select"
              >
                <SelectValue placeholder="Select gender" />
              </SelectTrigger>
              <SelectContent className="bg-cosmic-bg-secondary border-white/10">
                <SelectItem value="unknown">Prefer not to say</SelectItem>
                <SelectItem value="male">Male</SelectItem>
                <SelectItem value="female">Female</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          {/* Submit Button */}
          <Button
            type="submit"
            disabled={loading}
            className="w-full star-button py-6 h-auto text-lg mt-8"
            data-testid="generate-chart-btn"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                Calculating Your Chart...
              </span>
            ) : (
              'Generate Birth Chart'
            )}
          </Button>
        </form>
      </div>
    </div>
  );
};

export default ChartPage;
