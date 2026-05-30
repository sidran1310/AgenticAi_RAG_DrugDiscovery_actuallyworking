import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Index from './pages/Index';
import AuthCallback from './pages/AuthCallback';
import AuthError from './pages/AuthError';
import ErrorBoundary from './components/ErrorBoundary';
import { GlobalQueryProvider } from './contexts/GlobalQueryContext';
// MODULE_IMPORTS_START
// MODULE_IMPORTS_END

const queryClient = new QueryClient();

const App = () => (
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <GlobalQueryProvider>
        {/* MODULE_PROVIDERS_START */}
        {/* MODULE_PROVIDERS_END */}
        <TooltipProvider>
          <Toaster />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/auth/callback" element={<AuthCallback />} />
              <Route path="/auth/error" element={<AuthError />} />
              {/* MODULE_ROUTES_START */}
              {/* MODULE_ROUTES_END */}
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
        {/* MODULE_PROVIDERS_CLOSE */}
      </GlobalQueryProvider>
    </QueryClientProvider>
  </ErrorBoundary>
);

export default App;
