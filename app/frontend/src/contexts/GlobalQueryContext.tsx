import React, { createContext, useContext, useState, ReactNode } from 'react';

interface GlobalQueryContextType {
  query: string;
  setQuery: (query: string) => void;
  isProcessing: boolean;
  setIsProcessing: (processing: boolean) => void;
  results: {
    chat?: any;
    molecules?: any[];
    papers_graph?: any;
    papersGraph?: any;
    rag_results?: any[];
    ragResults?: any[];
    tools?: any[];
    toolsUsed?: any[];
    metadata?: any;
  };
  setResults: (results: Partial<GlobalQueryContextType['results']>) => void;
  autoDock: { compound: string; pdbId: string } | null;
  setAutoDock: (dock: { compound: string; pdbId: string } | null) => void;
}

const GlobalQueryContext = createContext<GlobalQueryContextType | undefined>(undefined);

export const useGlobalQuery = () => {
  const context = useContext(GlobalQueryContext);
  if (!context) {
    throw new Error('useGlobalQuery must be used within a GlobalQueryProvider');
  }
  return context;
};

interface GlobalQueryProviderProps {
  children: ReactNode;
}

export const GlobalQueryProvider: React.FC<GlobalQueryProviderProps> = ({ children }) => {
  const [query, setQuery] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResultsState] = useState<GlobalQueryContextType['results']>({});
  const [autoDock, setAutoDock] = useState<{ compound: string; pdbId: string } | null>(null);

  const setResults = (newResults: Partial<GlobalQueryContextType['results']>) => {
    setResultsState(prev => ({ ...prev, ...newResults }));
  };

  const value: GlobalQueryContextType = {
    query,
    setQuery,
    isProcessing,
    setIsProcessing,
    results,
    setResults,
    autoDock,
    setAutoDock,
  };

  return (
    <GlobalQueryContext.Provider value={value}>
      {children}
    </GlobalQueryContext.Provider>
  );
};
