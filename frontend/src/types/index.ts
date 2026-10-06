export interface Sheet {
  id: string;
  document_id: string;
  sheet_number: number;
  page_index: number;
  sheet_name: string;
  page_type: 'native' | 'scanned' | 'mixed' | string;
  width: number;
  height: number;
  image_url?: string;
  overlay_url?: string | null;
  components_count?: number;
  symbols_count?: number;
  ocr_count?: number;
  connections_count?: number;
  processing_status: string;
}

export interface ComponentItem {
  id: string;
  document_id: string;
  sheet_id: string;
  symbol_id?: string | null;
  ocr_result_id?: string | null;
  tag: string;
  component_name: string;
  component_type: 'Instrument' | 'Valve' | 'Equipment' | 'Connector' | string;
  symbol_class: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  center_x: number;
  center_y: number;
  confidence: number;
  association_score: number;
  distance_to_tag: number;
  source: string;
  validation_status: 'VALID' | 'WARNING' | 'ERROR' | string;
  validation_notes?: string;
  created_at?: string;
}

export interface ConnectionItem {
  id: string;
  sheet_id: string;
  source_component_id?: string | null;
  target_component_id?: string | null;
  source_tag?: string;
  target_tag?: string;
  source_type?: string;
  target_type?: string;
  line_label: string;
  line_type: string;
  start_x: number;
  start_y: number;
  end_x: number;
  end_y: number;
  path_points: number[][];
  confidence: number;
}

export interface CrossSheetConnectorItem {
  id: string;
  sheet_id: string;
  connector_label: string;
  target_sheet_number?: number | null;
  target_sheet_id?: string | null;
  connected_component_id?: string | null;
  connected_tag?: string | null;
  direction: 'in' | 'out' | 'bidirectional' | string;
  confidence: number;
  matched: boolean;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface ValidationIssue {
  id: string;
  sheet_id?: string | null;
  component_id?: string | null;
  component_tag?: string | null;
  rule_name: string;
  severity: 'VALID' | 'WARNING' | 'ERROR';
  message: string;
  details?: Record<string, any>;
  backtrack_suggested?: string;
  resolved: boolean;
  created_at?: string;
}

export interface ValidationSummary {
  valid_count: number;
  warning_count: number;
  error_count: number;
  total_components: number;
  issues: ValidationIssue[];
}

export interface ProcessingRun {
  id: string;
  document_id: string;
  current_stage: string;
  progress_percentage: number;
  stage_statuses: Record<string, { status: string; [key: string]: any }>;
  backtrack_count: number;
  backtrack_history: Array<{
    from_stage: string;
    to_stage: string;
    reason: string;
    timestamp: string;
  }>;
  error_message?: string;
  started_at?: string;
  completed_at?: string | null;
}

export interface DocumentItem {
  id: string;
  filename: string;
  file_path: string;
  file_size: number;
  page_count: number;
  doc_type: string;
  processing_status: 'uploaded' | 'processing' | 'completed' | 'failed' | string;
  created_at?: string;
  updated_at?: string;
  sheets?: Sheet[];
  processing_runs?: ProcessingRun[];
}
