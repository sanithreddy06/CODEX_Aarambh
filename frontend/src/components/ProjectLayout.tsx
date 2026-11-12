import React, { useEffect, useState } from 'react';
import { Outlet, useParams } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { api, Project } from '../lib/api';

export const ProjectLayout: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);

  useEffect(() => {
    if (id) {
      api.getProject(id).then(setProject).catch(console.error);
    }
  }, [id]);

  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] bg-[#0b0f17]">
      <Sidebar
        projectName={project?.name}
        primaryLang={project?.primary_language}
        healthScore={project?.health_score}
      />
      <main className="flex-1 overflow-x-hidden p-6">
        <Outlet context={{ project }} />
      </main>
    </div>
  );
};
