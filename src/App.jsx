import React, { useState, useEffect } from 'react';
import { collection, addDoc, onSnapshot, serverTimestamp, doc } from 'firebase/firestore';
import { db } from './firebase/config';
import FlightSearchForm from './components/FlightSearchForm';
import FlightResultsList from './components/FlightResultsList';

function App() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [currentCommandId, setCurrentCommandId] = useState(null);

  useEffect(() => {
    let unsubscribe;

    if (currentCommandId) {
      // Listen to the specific command document
      const docRef = doc(db, 'commands', currentCommandId);
      unsubscribe = onSnapshot(docRef, (docSnap) => {
        if (docSnap.exists()) {
          const data = docSnap.data();

          if (data.status === 'COMPLETED') {
            setResults(data.results || []);
            setLoading(false);
            setCurrentCommandId(null); // Stop listening once completed
          } else if (data.status === 'ERROR') {
            setError(data.error_message || 'An error occurred during the search.');
            setLoading(false);
            setCurrentCommandId(null);
          }
        }
      });
    }

    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, [currentCommandId]);

  const handleSearch = async (searchParams) => {
    setLoading(true);
    setError(null);
    setResults([]);

    try {
      // 1. Write the command to Firestore
      const docRef = await addDoc(collection(db, 'commands'), {
        type: 'SEARCH_FLIGHTS',
        status: 'PENDING',
        params: searchParams,
        createdAt: serverTimestamp()
      });

      // 2. Save the ID to start listening via useEffect
      setCurrentCommandId(docRef.id);

    } catch (err) {
      console.error("Error creating command:", err);
      setError("Failed to connect to the database.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold text-indigo-600">FlightHunter</h1>
          <p className="mt-2 text-lg text-gray-600">Find the best flight deals using Amadeus API</p>
        </div>

        <FlightSearchForm onSearch={handleSearch} loading={loading} />

        {error && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4">
            <div className="flex">
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {loading && !error && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <p className="mt-2 text-gray-500">Waiting for backend to process your request...</p>
          </div>
        )}

        {!loading && !error && results.length > 0 && (
          <FlightResultsList results={results} />
        )}
      </div>
    </div>
  );
}

export default App;
