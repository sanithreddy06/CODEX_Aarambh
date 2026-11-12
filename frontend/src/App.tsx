import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { UploadPage } from './pages/UploadPage';
import { SettingsPage } from './pages/SettingsPage';
import { ProjectLayout } from './components/ProjectLayout';
import { OverviewPage } from './pages/OverviewPage';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { DependenciesPage } from './pages/DependenciesPage';
import { CodeExplorerPage } from './pages/CodeExplorerPage';
import { DatabasePage } from './pages/DatabasePage';
import { ApiExplorerPage } from './pages/ApiExplorerPage';
import { WorkflowsPage } from './pages/WorkflowsPage';
import { HealthPage } from './pages/HealthPage';
import { AssistantPage } from './pages/AssistantPage';
import { DocumentationPage } from './pages/DocumentationPage';
import { TestsPage } from './pages/TestsPage';

export function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#0b0f17] text-neutral-200 flex flex-col">
        <Navbar />
        <div className="flex-1">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/settings" element={<SettingsPage />} />

            <Route path="/projects/:id" element={<ProjectLayout />}>
              <Route index element={<OverviewPage />} />
              <Route path="architecture" element={<ArchitecturePage />} />
              <Route path="dependencies" element={<DependenciesPage />} />
              <Route path="code" element={<CodeExplorerPage />} />
              <Route path="database" element={<DatabasePage />} />
              <Route path="apis" element={<ApiExplorerPage />} />
              <Route path="workflows" element={<WorkflowsPage />} />
              <Route path="health" element={<HealthPage />} />
              <Route path="assistant" element={<AssistantPage />} />
              <Route path="docs" element={<DocumentationPage />} />
              <Route path="tests" element={<TestsPage />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
