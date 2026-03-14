import React from 'react';

const FlightResultsList = ({ results }) => {
  if (!results || results.length === 0) {
    return <div className="text-center text-gray-500 mt-8">No flight results to display.</div>;
  }

  return (
    <div className="mt-6 space-y-4">
      <h2 className="text-2xl font-semibold text-gray-800">Search Results</h2>
      {results.map((flight, index) => (
        <div key={flight.id || index} className="bg-white p-4 rounded-lg border shadow-sm hover:shadow-md transition-shadow">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
            <div className="font-medium text-indigo-600">{flight.itineraries[0].segments[0].carrierCode} {flight.itineraries[0].segments[0].aircraft.code}</div>
            <div>
              <div className="text-sm text-gray-500">Duration</div>
              <div className="font-semibold">{flight.itineraries[0].duration.replace('PT', '').replace('H', 'h ').replace('M', 'm')}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Stops</div>
              <div className="font-semibold">{flight.itineraries[0].segments.length - 1}</div>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-gray-800">{flight.price.total} {flight.price.currency}</div>
              <a
                href="#"
                onClick={(e) => e.preventDefault()}
                className="text-sm text-indigo-600 hover:underline"
              >
                Select Flight
              </a>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default FlightResultsList;
