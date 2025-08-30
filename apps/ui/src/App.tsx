import React, { useState, useEffect } from 'react';

interface Place {
  id: number;
  name: string;
  summary_160: string;
  tags_json: string[];
  lat: number;
  lng: number;
}

interface Route {
  steps: number[];
  total_distance_m: number;
  fit_score: number;
}

interface Alternative {
  id: number;
  name: string;
  similarity: number;
}

interface RouteResponse {
  routes: Route[];
  alternatives: {
    step2?: Alternative[];
  };
}

const App: React.FC = () => {
  const [vibeQuery, setVibeQuery] = useState('');
  const [selectedVibe, setSelectedVibe] = useState('');
  const [selectedIntents, setSelectedIntents] = useState<string[]>([]);
  const [routeData, setRouteData] = useState<RouteResponse | null>(null);
  const [places, setPlaces] = useState<Place[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const vibeOptions = ['Lazy', 'Cozy', 'Scenic', 'Budget', 'Date'];
  const quickIntents = [
    { emoji: '🍜', text: 'Tom Yum', value: 'tom-yum' },
    { emoji: '🌿', text: 'Park Walk', value: 'walk' },
    { emoji: '🍸', text: 'Rooftop', value: 'rooftop' }
  ];

  // Hardcoded Bangkok coordinates
  const defaultLat = 13.7563;
  const defaultLng = 100.5018;

  const fetchPlaces = async (placeIds: number[]) => {
    try {
      const placePromises = placeIds.map(id => 
        fetch(`/api/places/${id}`).then(res => res.json())
      );
      const placeData = await Promise.all(placePromises);
      setPlaces(placeData);
    } catch (err) {
      console.error('Error fetching places:', err);
    }
  };

  const buildRoute = async () => {
    if (!selectedVibe && !vibeQuery.trim()) {
      setError('Please select a vibe or enter a vibe query');
      return;
    }

    if (selectedIntents.length === 0) {
      setError('Please select at least one intent');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const vibe = selectedVibe || vibeQuery.trim();
      const intents = selectedIntents.join(',');
      
      const response = await fetch(
        `/api/places/recommend?vibe=${encodeURIComponent(vibe)}&intents=${encodeURIComponent(intents)}&lat=${defaultLat}&lng=${defaultLng}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: RouteResponse = await response.json();
      setRouteData(data);
      
      // Fetch place details for the route
      if (data.routes && data.routes[0]) {
        await fetchPlaces(data.routes[0].steps);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to build route');
    } finally {
      setLoading(false);
    }
  };

  const replaceStep2 = async () => {
    if (!routeData?.alternatives?.step2 || routeData.alternatives.step2.length === 0) {
      return;
    }

    setLoading(true);
    try {
      // Get the first alternative for step 2
      const alternative = routeData.alternatives.step2[0];
      
      // Create new route with alternative step 2
      if (routeData.routes[0]) {
        const newRoute = {
          ...routeData.routes[0],
          steps: [routeData.routes[0].steps[0], alternative.id, routeData.routes[0].steps[2]]
        };
        
        const newRouteData = {
          ...routeData,
          routes: [newRoute]
        };
        
        setRouteData(newRouteData);
        
        // Fetch updated place details
        await fetchPlaces(newRoute.steps);
      }
    } catch (err) {
      setError('Failed to replace step 2');
    } finally {
      setLoading(false);
    }
  };

  const handleVibeClick = (vibe: string) => {
    setSelectedVibe(vibe);
    setVibeQuery('');
  };

  const handleIntentClick = (intent: string) => {
    setSelectedIntents(prev => 
      prev.includes(intent) 
        ? prev.filter(i => i !== intent)
        : [...prev, intent]
    );
  };

  const getDistanceToNext = (currentIndex: number): string => {
    if (!routeData?.routes[0] || currentIndex >= routeData.routes[0].steps.length - 1) {
      return '0m';
    }
    
    // For demo purposes, return a mock distance
    // In a real app, you'd calculate actual distances
    return `${Math.floor(Math.random() * 500 + 200)}m`;
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center p-6">
      <div className="max-w-4xl w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-2">Entertainment Planner</h1>
          <p className="text-gray-400">Discover amazing places in Bangkok</p>
        </div>

        {/* Vibe Selection */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Choose your vibe</h2>
          <div className="flex flex-wrap gap-3">
            {vibeOptions.map((vibe) => (
              <button
                key={vibe}
                onClick={() => handleVibeClick(vibe)}
                className={`px-4 py-2 rounded-full border transition-colors ${
                  selectedVibe === vibe
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'border-gray-600 text-gray-300 hover:border-gray-500'
                }`}
              >
                {vibe}
              </button>
            ))}
          </div>
          
          {/* Custom vibe input */}
          <div className="mt-4">
            <input
              type="text"
              placeholder="Or type your own vibe..."
              value={vibeQuery}
              onChange={(e) => setVibeQuery(e.target.value)}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Quick Intents */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">What do you want to do?</h2>
          <div className="flex flex-wrap gap-3">
            {quickIntents.map((intent) => (
              <button
                key={intent.value}
                onClick={() => handleIntentClick(intent.value)}
                className={`px-4 py-2 rounded-full border transition-colors ${
                  selectedIntents.includes(intent.value)
                    ? 'bg-green-600 border-green-600 text-white'
                    : 'border-gray-600 text-gray-300 hover:border-gray-500'
                }`}
              >
                <span className="mr-2">{intent.emoji}</span>
                {intent.text}
              </button>
            ))}
          </div>
        </div>

        {/* Build Route Button */}
        <div className="text-center">
          <button
            onClick={buildRoute}
            disabled={loading}
            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg font-semibold text-lg transition-colors"
          >
            {loading ? 'Building Route...' : 'Build Route'}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-2 rounded-lg">
            {error}
          </div>
        )}

        {/* Route Display */}
        {routeData && places.length > 0 && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold">Your Route</h2>
              {routeData.alternatives?.step2 && routeData.alternatives.step2.length > 0 && (
                <button
                  onClick={replaceStep2}
                  disabled={loading}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg font-medium transition-colors"
                >
                  Replace Step 2
                </button>
              )}
            </div>
            
            <div className="grid gap-6">
              {places.map((place, index) => (
                <div key={place.id} className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-2xl font-bold text-blue-400">#{index + 1}</span>
                        <h3 className="text-xl font-semibold">{place.name}</h3>
                      </div>
                      <p className="text-gray-300 mb-3">{place.summary_160}</p>
                      <div className="flex flex-wrap gap-2 mb-3">
                        {place.tags_json?.map((tag, tagIndex) => (
                          <span
                            key={tagIndex}
                            className="px-2 py-1 bg-gray-700 text-gray-300 text-sm rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                      {index < places.length - 1 && (
                        <div className="text-sm text-gray-400">
                          → {getDistanceToNext(index)} to next place
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Route Summary */}
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
              <div className="flex justify-between items-center text-sm text-gray-400">
                <span>Total Distance: {routeData.routes[0]?.total_distance_m || 0}m</span>
                <span>Fit Score: {(routeData.routes[0]?.fit_score || 0).toFixed(3)}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
