import { PATHS } from '@/constants/path.ts';
import { Navigate } from 'react-router-dom';
import { DataSetupPage } from './pages/DataSetupPage';
import { AnalyzingPage } from './pages/AnalyzingPage';
import { ReportPage } from './pages/ReportPage';

export const appRoutes = [
  { path: PATHS.DATA_SETUP, element: <DataSetupPage /> },
  { path: PATHS.ANALYZING, element: <AnalyzingPage /> },
  { path: PATHS.REPORT, element: <ReportPage /> },
  { path: '*', element: <Navigate to={PATHS.DATA_SETUP} replace /> },
];
