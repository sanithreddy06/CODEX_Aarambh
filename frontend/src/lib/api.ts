export interface Project {
  id: string;
  name: string;
  description: string;
  original_archive_name: string;
  status: 'pending' | 'scanning' | 'analyzing' | 'completed' | 'failed';
  error_message: string;
  total_files: number;
  total_lines: number;
  primary_language: string;
  languages: Array<{ language: string; file_count: number; line_count: number; percentage: number }>;
  frameworks: Array<{ name: string; type: string; version?: string; evidence?: string }>;
  ignored_files_count: number;
  health_score: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectOverview {
  project: Project;
  files_count: number;
  lines_count: number;
  endpoints_count: number;
  models_count: number;
  entities_count: number;
  components_count: number;
  health_score: number;
  categories_breakdown: Record<string, number>;
  layers_breakdown: Record<string, number>;
}

export interface FileRecord {
  id: string;
  project_id: string;
  relative_path: string;
  language: string;
  size_bytes: number;
  line_count: number;
  category: string;
  layer: string;
  is_entry_point: boolean;
}

export interface AstEntity {
  id: string;
  file_path: string;
  name: string;
  entity_type: string;
  start_line: number;
  end_line: number;
  language: string;
  signature: string;
  docstring: string;
  params: any[];
  calls: string[];
  evidence: any;
}

export interface AstTree {
  name: string;
  type: string;
  line?: number;
  details?: string;
  children?: AstTree[];
}

export interface DependencyNode {
  id: string;
  label: string;
  type: string;
  language?: string;
  layer?: string;
  line_count?: number;
}

export interface DependencyEdge {
  id: string;
  source: string;
  target: string;
  edge_type: string;
  confidence: string;
  evidence: any;
}

export interface DependencyGraphData {
  nodes: DependencyNode[];
  edges: DependencyEdge[];
  circular_dependencies: string[][];
  high_dependency_modules: Array<{
    node_id: string;
    label: string;
    in_degree: number;
    out_degree: number;
    total_degree: number;
    centrality_role: string;
  }>;
  isolated_modules: string[];
}

export interface ImpactAnalysis {
  target_node: string;
  direct_dependents: string[];
  indirect_dependents: string[];
  affected_files: string[];
  severity: 'low' | 'medium' | 'high' | 'critical';
  evidence: Array<{
    dependent: string;
    depends_on: string;
    relationship: string;
    depth: number;
  }>;
}

export interface ArchitectureComponent {
  id: string;
  name: string;
  layer: string;
  files: string[];
  responsibilities: string[];
  incoming_connections: string[];
  outgoing_connections: string[];
  evidence: any;
}

export interface ArchitectureData {
  layers: string[];
  components: ArchitectureComponent[];
  connections: Array<{ source_layer: string; target_layer: string; description: string }>;
}

export interface DatabaseModel {
  name: string;
  table_name: string;
  orm_framework: string;
  file_path: string;
  line_number: number;
  fields: Array<{ name: string; type: string; primary_key?: boolean; foreign_key?: string; nullable?: boolean }>;
  relationships: Array<{ target: string; type: string; confidence: string; evidence: string }>;
  evidence: any;
}

export interface DatabaseSchemaData {
  models: DatabaseModel[];
  er_nodes: any[];
  er_edges: any[];
}

export interface ApiEndpoint {
  id: string;
  method: string;
  path: string;
  framework: string;
  file_path: string;
  line_number: number;
  handler_name: string;
  auth_middleware: string;
  parameters: Array<{ name: string; in: string; required: boolean; type?: string }>;
  request_schema: any;
  response_schema: any;
  related_models: string[];
  evidence: any;
}

export interface ApiExplorerData {
  endpoints: ApiEndpoint[];
  total_endpoints: number;
  frameworks: string[];
  methods: Record<string, number>;
  openapi_spec: any;
}

export interface WorkflowSequence {
  id: string;
  name: string;
  trigger: string;
  steps: Array<{ order: number; component: string; action: string; file: string; line: number; layer?: string }>;
  evidence: any;
}

export interface HealthReport {
  health_score: number;
  grade: string;
  findings: Array<{
    id: string;
    category: string;
    title: string;
    description: string;
    severity: string;
    affected_files: string[];
    evidence: any;
  }>;
  summary_by_severity: Record<string, number>;
  summary_by_category: Record<string, number>;
}

export interface GeneratedTest {
  id: string;
  target_file: string;
  target_symbol: string;
  test_framework: string;
  test_type: string;
  test_name: string;
  code: string;
  review_status: string;
  created_at: string;
}

const API_BASE = '/api';

export const api = {
  // Projects
  async getProjects(): Promise<Project[]> {
    const res = await fetch(`${API_BASE}/projects`);
    if (!res.ok) throw new Error('Failed to fetch projects');
    return res.json();
  },

  async getProject(id: string): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects/${id}`);
    if (!res.ok) throw new Error('Failed to fetch project');
    return res.json();
  },

  async uploadProject(name: string, description: string, file: File): Promise<Project> {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('description', description);
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/projects/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async deleteProject(id: string): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE}/projects/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete project');
    return res.json();
  },

  async triggerAnalysis(id: string): Promise<any> {
    const res = await fetch(`${API_BASE}/projects/${id}/analyze`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to trigger analysis');
    return res.json();
  },

  async getAnalysisStatus(id: string): Promise<{ status: string; error_message: string; health_score: number; total_files: number }> {
    const res = await fetch(`${API_BASE}/projects/${id}/analysis/status`);
    if (!res.ok) throw new Error('Failed to get status');
    return res.json();
  },

  async getProjectOverview(id: string): Promise<ProjectOverview> {
    const res = await fetch(`${API_BASE}/projects/${id}/overview`);
    if (!res.ok) throw new Error('Failed to get overview');
    return res.json();
  },

  async getProjectFiles(id: string): Promise<FileRecord[]> {
    const res = await fetch(`${API_BASE}/projects/${id}/files`);
    if (!res.ok) throw new Error('Failed to get files');
    return res.json();
  },

  async getFileContent(id: string, path: string): Promise<{ content: string; file_path: string }> {
    const res = await fetch(`${API_BASE}/projects/${id}/file-content?file_path=${encodeURIComponent(path)}`);
    if (!res.ok) throw new Error('Failed to get file content');
    return res.json();
  },

  async getAst(id: string, filePath?: string): Promise<{ entities: AstEntity[]; ast_tree?: AstTree }> {
    const url = filePath
      ? `${API_BASE}/projects/${id}/ast?file_path=${encodeURIComponent(filePath)}`
      : `${API_BASE}/projects/${id}/ast`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to get AST');
    return res.json();
  },

  async getDependencies(id: string): Promise<DependencyGraphData> {
    const res = await fetch(`${API_BASE}/projects/${id}/dependencies`);
    if (!res.ok) throw new Error('Failed to get dependencies');
    return res.json();
  },

  async analyzeImpact(id: string, nodeId: string, depth: number = 3): Promise<ImpactAnalysis> {
    const res = await fetch(`${API_BASE}/projects/${id}/dependencies/impact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ node_id: nodeId, depth }),
    });
    if (!res.ok) throw new Error('Failed to run impact analysis');
    return res.json();
  },

  async getArchitecture(id: string): Promise<ArchitectureData> {
    const res = await fetch(`${API_BASE}/projects/${id}/architecture`);
    if (!res.ok) throw new Error('Failed to get architecture');
    return res.json();
  },

  async getDatabaseSchema(id: string): Promise<DatabaseSchemaData> {
    const res = await fetch(`${API_BASE}/projects/${id}/database`);
    if (!res.ok) throw new Error('Failed to get database schema');
    return res.json();
  },

  async getApis(id: string): Promise<ApiExplorerData> {
    const res = await fetch(`${API_BASE}/projects/${id}/apis`);
    if (!res.ok) throw new Error('Failed to get APIs');
    return res.json();
  },

  async getWorkflows(id: string): Promise<{ workflows: WorkflowSequence[] }> {
    const res = await fetch(`${API_BASE}/projects/${id}/workflows`);
    if (!res.ok) throw new Error('Failed to get workflows');
    return res.json();
  },

  async getHealth(id: string): Promise<HealthReport> {
    const res = await fetch(`${API_BASE}/projects/${id}/health`);
    if (!res.ok) throw new Error('Failed to get health report');
    return res.json();
  },

  async sendChatMessage(id: string, message: string, history: any[] = []): Promise<{ message: string; sources: any[]; confidence: string; provider_used: string }> {
    const res = await fetch(`${API_BASE}/projects/${id}/assistant/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history }),
    });
    if (!res.ok) throw new Error('Failed to send chat message');
    return res.json();
  },

  async getDocumentation(id: string): Promise<{ markdown: string; project_id: string }> {
    const res = await fetch(`${API_BASE}/projects/${id}/documentation`);
    if (!res.ok) throw new Error('Failed to get documentation');
    return res.json();
  },

  async getGeneratedTests(id: string): Promise<GeneratedTest[]> {
    const res = await fetch(`${API_BASE}/projects/${id}/tests`);
    if (!res.ok) throw new Error('Failed to get tests');
    return res.json();
  },

  async generateTests(id: string, targetFile?: string, framework: string = 'pytest'): Promise<GeneratedTest[]> {
    const res = await fetch(`${API_BASE}/projects/${id}/tests/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_file: targetFile, framework }),
    });
    if (!res.ok) throw new Error('Failed to generate tests');
    return res.json();
  }
};
