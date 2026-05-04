export type AppType = "chatbot" | "agent" | "workflow";

export interface App {
  id: string;
  name: string;
  description: string;
  type: AppType;
  model_provider_id: string;
  model_name: string;
  created_at: string;
  updated_at: string;
}

export type AppCreateRequest = Pick<
  App,
  "name" | "description" | "type" | "model_provider_id" | "model_name"
>;
