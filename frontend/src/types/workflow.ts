export type NodeType =
  | "llm"
  | "knowledge"
  | "http"
  | "code"
  | "condition"
  | "template"
  | "variable";

export interface WorkflowNode {
  id: string;
  type: NodeType;
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  created_at: string;
  updated_at: string;
}

export type WorkflowCreateRequest = Pick<
  Workflow,
  "name" | "description" | "nodes" | "edges"
>;
