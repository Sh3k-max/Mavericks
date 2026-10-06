import {
  DocumentItem,
  Sheet,
  ComponentItem,
  ConnectionItem,
  CrossSheetConnectorItem,
  ValidationSummary,
  ProcessingRun
} from '../types';

const BASE_URL = '';

export const api = {
  async getDocuments(): Promise<DocumentItem[]> {
    const res = await fetch(`${BASE_URL}/api/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async getDocument(id: string): Promise<DocumentItem> {
    const res = await fetch(`${BASE_URL}/api/documents/${id}`);
    if (!res.ok) throw new Error('Failed to fetch document details');
    return res.json();
  },

  async getDocumentStatus(id: string): Promise<{
    document_id: string;
    status: string;
    progress_percentage: number;
    current_stage: string;
    stage_statuses: Record<string, any>;
    backtrack_count: number;
    backtrack_history: any[];
    error_message?: string;
  }> {
    const res = await fetch(`${BASE_URL}/api/documents/${id}/status`);
    if (!res.ok) throw new Error('Failed to fetch processing status');
    return res.json();
  },

  async uploadDocument(file: File, autoProcess = true): Promise<{ id: string; filename: string }> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/api/documents/upload?auto_process=${autoProcess}`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async triggerDemo(): Promise<{ id: string; filename: string; message: string }> {
    const res = await fetch(`${BASE_URL}/api/documents/demo`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to initialize synthetic demo P&ID');
    return res.json();
  },

  async processDocument(id: string): Promise<void> {
    const res = await fetch(`${BASE_URL}/api/documents/${id}/process`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to start document processing');
  },

  async getSheets(id: string): Promise<Sheet[]> {
    const res = await fetch(`${BASE_URL}/api/documents/${id}/sheets`);
    if (!res.ok) throw new Error('Failed to fetch sheets');
    return res.json();
  },

  async getComponents(
    id: string,
    filters?: {
      sheet_id?: string;
      component_type?: string;
      status?: string;
      search?: string;
    }
  ): Promise<ComponentItem[]> {
    const params = new URLSearchParams();
    if (filters?.sheet_id) params.append('sheet_id', filters.sheet_id);
    if (filters?.component_type) params.append('component_type', filters.component_type);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.search) params.append('search', filters.search);

    const res = await fetch(`${BASE_URL}/api/documents/${id}/components?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch components');
    return res.json();
  },

  async getConnections(id: string, sheetId?: string): Promise<ConnectionItem[]> {
    const url = sheetId
      ? `${BASE_URL}/api/documents/${id}/connections?sheet_id=${sheetId}`
      : `${BASE_URL}/api/documents/${id}/connections`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch connections');
    return res.json();
  },

  async getCrossSheetConnectors(id: string): Promise<CrossSheetConnectorItem[]> {
    const res = await fetch(`${BASE_URL}/api/documents/${id}/cross-sheet`);
    if (!res.ok) throw new Error('Failed to fetch cross-sheet connectors');
    return res.json();
  },

  async getValidation(id: string): Promise<ValidationSummary> {
    const res = await fetch(`${BASE_URL}/api/documents/${id}/validation`);
    if (!res.ok) throw new Error('Failed to fetch validation summary');
    return res.json();
  },

  getExportExcelUrl(id: string): string {
    return `${BASE_URL}/api/documents/${id}/export/excel`;
  },

  getExportCsvUrl(id: string): string {
    return `${BASE_URL}/api/documents/${id}/export/csv`;
  },

  getExportJsonUrl(id: string): string {
    return `${BASE_URL}/api/documents/${id}/export/json`;
  },

  getSheetImageUrl(sheetId: string): string {
    return `${BASE_URL}/api/documents/image/${sheetId}`;
  },

  getSheetOverlayUrl(docId: string, sheetId: string): string {
    return `${BASE_URL}/api/documents/${docId}/overlay/${sheetId}`;
  }
};
