import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Dashboard } from './components/Dashboard';
import { SheetViewer } from './components/SheetViewer';
import { ComponentExplorer } from './components/ComponentExplorer';
import { ConnectivityView } from './components/ConnectivityView';
import { ValidationView } from './components/ValidationView';
import { ProcessingMonitor } from './components/ProcessingMonitor';
import { UploadModal } from './components/UploadModal';
import { DocumentItem, Sheet } from './types';
import { api } from './services/api';

export function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);
  const [sheets, setSheets] = useState<Sheet[]>([]);
  const [selectedSheet, setSelectedSheet] = useState<Sheet | null>(null);

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isDemoLoading, setIsDemoLoading] = useState(false);
  const [notification, setNotification] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const showNotification = (text: string, type: 'success' | 'error' = 'success') => {
    setNotification({ text, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const loadDocuments = async () => {
    try {
      const docs = await api.getDocuments();
      setDocuments(docs);
      if (docs.length > 0 && !selectedDoc) {
        setSelectedDoc(docs[0]);
      } else if (selectedDoc) {
        const refreshed = docs.find(d => d.id === selectedDoc.id);
        if (refreshed) setSelectedDoc(refreshed);
      }
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  // When selectedDoc changes, load its sheets
  useEffect(() => {
    if (!selectedDoc) {
      setSheets([]);
      setSelectedSheet(null);
      return;
    }

    const loadSheets = async () => {
      try {
        const sheetList = await api.getSheets(selectedDoc.id);
        setSheets(sheetList);
        if (sheetList.length > 0) {
          setSelectedSheet(sheetList[0]);
        } else {
          setSelectedSheet(null);
        }
      } catch (err) {
        console.error('Failed to load sheets:', err);
      }
    };

    loadSheets();
  }, [selectedDoc]);

  const handleUpload = async (file: File, autoProcess: boolean) => {
    try {
      const res = await api.uploadDocument(file, autoProcess);
      showNotification(`Document ${file.name} uploaded successfully!`);
      await loadDocuments();
      const updatedDocs = await api.getDocuments();
      const newDoc = updatedDocs.find(d => d.id === res.id);
      if (newDoc) {
        setSelectedDoc(newDoc);
        if (autoProcess) setCurrentTab('monitor');
      }
    } catch (err: any) {
      showNotification(err.message || 'Upload failed', 'error');
      throw err;
    }
  };

  const handleTriggerDemo = async () => {
    setIsDemoLoading(true);
    try {
      const res = await api.triggerDemo();
      showNotification('Synthetic multi-sheet P&ID generated! Pipeline running.');
      await loadDocuments();
      const updatedDocs = await api.getDocuments();
      const newDoc = updatedDocs.find(d => d.id === res.id);
      if (newDoc) {
        setSelectedDoc(newDoc);
        setCurrentTab('monitor');
      }
    } catch (err: any) {
      showNotification(err.message || 'Demo failed', 'error');
    } finally {
      setIsDemoLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#080b11] text-slate-100 flex flex-col font-sans">
      {/* Toast Notification */}
      {notification && (
        <div className={`fixed bottom-5 right-5 z-50 px-4 py-2.5 rounded-xl shadow-2xl text-xs font-mono border backdrop-blur animate-in slide-in-from-bottom duration-200 ${
          notification.type === 'success'
            ? 'bg-emerald-950/90 text-emerald-300 border-emerald-500/30 shadow-emerald-950/50'
            : 'bg-rose-950/90 text-rose-300 border-rose-500/30 shadow-rose-950/50'
        }`}>
          {notification.text}
        </div>
      )}

      {/* Navigation Bar */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        documents={documents}
        selectedDoc={selectedDoc}
        onSelectDoc={setSelectedDoc}
        onOpenUpload={() => setIsUploadOpen(true)}
        onTriggerDemo={handleTriggerDemo}
        isDemoLoading={isDemoLoading}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentTab === 'dashboard' && (
          <Dashboard
            documents={documents}
            selectedDoc={selectedDoc}
            onSelectDoc={setSelectedDoc}
            onOpenUpload={() => setIsUploadOpen(true)}
            onTriggerDemo={handleTriggerDemo}
            onNavigateTab={setCurrentTab}
            isDemoLoading={isDemoLoading}
          />
        )}

        {currentTab === 'viewer' && (
          <SheetViewer
            document={selectedDoc}
            sheets={sheets}
            selectedSheet={selectedSheet}
            onSelectSheet={setSelectedSheet}
          />
        )}

        {currentTab === 'components' && (
          <ComponentExplorer
            document={selectedDoc}
            sheets={sheets}
          />
        )}

        {currentTab === 'connectivity' && (
          <ConnectivityView
            document={selectedDoc}
            sheets={sheets}
          />
        )}

        {currentTab === 'validation' && (
          <ValidationView
            document={selectedDoc}
          />
        )}

        {currentTab === 'monitor' && (
          <ProcessingMonitor
            document={selectedDoc}
            onRefresh={loadDocuments}
          />
        )}
      </main>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUpload={handleUpload}
        onTriggerDemo={handleTriggerDemo}
      />

      {/* Footer */}
      <footer className="border-t border-white/5 py-4 text-center text-xs font-mono text-slate-500">
        P&ID Document Intelligence & Component Extraction System &copy; 2026 | Built with FastAPI, OpenCV, PyMuPDF & React
      </footer>
    </div>
  );
}

export default App;
