import React, { useEffect, useState } from 'react';
import { ApiClient } from '../services/api';
import { KnowledgeDoc, Merchant } from '../types';
import { 
  BookOpen, 
  Upload, 
  Plus, 
  Trash2, 
  CheckCircle2, 
  XCircle, 
  FileText, 
  AlertCircle,
  Eye,
  FileCode,
  FileSpreadsheet
} from 'lucide-react';

interface KnowledgePageProps {
  activeMerchant: Merchant | null;
}

export const KnowledgePage: React.FC<KnowledgePageProps> = ({ activeMerchant }) => {
  const [docs, setDocs] = useState<KnowledgeDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'all' | 'faq' | 'policy' | 'offer'>('all');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showFaqModal, setShowFaqModal] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDoc | null>(null);

  // Form states
  const [faqTitle, setFaqTitle] = useState('');
  const [faqContent, setFaqContent] = useState('');
  const [faqType, setFaqType] = useState('faq');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');

  const loadDocs = () => {
    setLoading(true);
    ApiClient.getKnowledgeDocs(activeTab === 'all' ? undefined : activeTab)
      .then((data) => {
        if (Array.isArray(data)) setDocs(data);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadDocs();
  }, [activeMerchant, activeTab]);

  const handleCreateFaq = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!faqTitle || !faqContent) return;

    await ApiClient.createFAQ(faqTitle, faqContent, faqType);
    setFaqTitle('');
    setFaqContent('');
    setShowFaqModal(false);
    loadDocs();
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setUploadError('');
    try {
      const res = await ApiClient.uploadDocument(uploadFile, uploadTitle || undefined);
      if (res.error) {
        setUploadError(res.error);
      } else {
        setShowUploadModal(false);
        setUploadFile(null);
        setUploadTitle('');
        loadDocs();
      }
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const togglePublish = async (doc: KnowledgeDoc) => {
    await ApiClient.togglePublishDoc(doc.id, !doc.is_published);
    loadDocs();
  };

  const handleDelete = async (docId: string) => {
    if (confirm('Are you sure you want to delete this document?')) {
      await ApiClient.deleteDoc(docId);
      loadDocs();
    }
  };

  const getDocIcon = (type: string) => {
    if (type === 'pdf') return <FileText className="w-5 h-5 text-rose-400" />;
    if (type === 'csv') return <FileSpreadsheet className="w-5 h-5 text-emerald-400" />;
    if (type === 'json') return <FileCode className="w-5 h-5 text-amber-400" />;
    return <BookOpen className="w-5 h-5 text-cyan-400" />;
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-emerald-400" />
            <span>Knowledge Base & Document Ingestion</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Upload policies, FAQs, and pricing documents. Authoritative inventory & slots are managed in business records.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowFaqModal(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-sm border border-slate-700 transition"
          >
            <Plus className="w-4 h-4" />
            <span>Add FAQ / Policy</span>
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm shadow-lg shadow-emerald-600/20 transition"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        {(['all', 'faq', 'policy', 'offer'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition ${
              activeTab === tab
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            {tab === 'all' ? 'All Documents' : `${tab}s`}
          </button>
        ))}
      </div>

      {/* Document List */}
      {loading ? (
        <div className="py-12 flex justify-center text-slate-400">Loading knowledge base...</div>
      ) : docs.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-800/30 border border-slate-800/60">
          <BookOpen className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-300">No documents found</h3>
          <p className="text-sm text-slate-500 mt-1">Upload PDF, TXT, CSV, or write an FAQ to expand Nexa's knowledge.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {docs.map((doc) => (
            <div
              key={doc.id}
              className="p-5 rounded-2xl bg-slate-800/60 border border-slate-800 hover:border-slate-700 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
                      {getDocIcon(doc.doc_type)}
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm text-white line-clamp-1">{doc.title}</h4>
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                        {doc.doc_type}
                      </span>
                    </div>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      doc.is_published
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-slate-700 text-slate-400'
                    }`}
                  >
                    {doc.is_published ? 'Published' : 'Draft'}
                  </span>
                </div>

                <p className="text-xs text-slate-300 mt-3 line-clamp-3 leading-relaxed">
                  {doc.content}
                </p>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
                <button
                  onClick={() => setSelectedDoc(doc)}
                  className="flex items-center gap-1.5 hover:text-white transition"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Preview</span>
                </button>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => togglePublish(doc)}
                    className="hover:text-emerald-400 transition"
                  >
                    {doc.is_published ? 'Unpublish' : 'Publish'}
                  </button>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="p-1 rounded hover:bg-rose-500/10 text-rose-400 transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-1">Upload Knowledge Document</h3>
            <p className="text-xs text-slate-400 mb-4">
              Supported formats: PDF, TXT, Markdown, CSV, JSON.
            </p>

            {uploadError && (
              <div className="p-3 mb-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}

            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Document Title (Optional)</label>
                <input
                  type="text"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  placeholder="e.g. 2026 Customer Service Guidelines"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Select File</label>
                <input
                  type="file"
                  accept=".pdf,.txt,.md,.csv,.json"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm file:mr-4 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-600 file:text-white hover:file:bg-emerald-500"
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-semibold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition flex items-center gap-2"
                >
                  {uploading ? 'Processing...' : 'Upload & Extract'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add FAQ Modal */}
      {showFaqModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-1">Add FAQ / Policy Item</h3>
            <p className="text-xs text-slate-400 mb-4">Structured notes used by Nexa to answer inquiries.</p>

            <form onSubmit={handleCreateFaq} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Type</label>
                <select
                  value={faqType}
                  onChange={(e) => setFaqType(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                >
                  <option value="faq">FAQ</option>
                  <option value="policy">Store Policy</option>
                  <option value="offer">Promotional Notice</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Title / Question</label>
                <input
                  type="text"
                  value={faqTitle}
                  onChange={(e) => setFaqTitle(e.target.value)}
                  placeholder="e.g. What is the return policy?"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Content / Answer</label>
                <textarea
                  value={faqContent}
                  onChange={(e) => setFaqContent(e.target.value)}
                  rows={4}
                  placeholder="Provide authoritative store policy or answer details..."
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowFaqModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-semibold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition"
                >
                  Save Document
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl p-6 shadow-2xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div>
                <h3 className="text-lg font-bold text-white">{selectedDoc.title}</h3>
                <span className="text-xs text-slate-400 capitalize">{selectedDoc.doc_type}</span>
              </div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="py-4 overflow-y-auto flex-1 text-sm text-slate-200 leading-relaxed font-mono whitespace-pre-wrap bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 my-4">
              {selectedDoc.content}
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setSelectedDoc(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold transition"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
