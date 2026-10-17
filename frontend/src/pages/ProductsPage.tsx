import React, { useEffect, useState } from 'react';
import { ApiClient } from '../services/api';
import { CatalogItem, Merchant } from '../types';
import { Package, Plus, Search, Tag, DollarSign, Layers, CheckCircle, Clock, Trash2 } from 'lucide-react';

interface ProductsPageProps {
  activeMerchant: Merchant | null;
}

export const ProductsPage: React.FC<ProductsPageProps> = ({ activeMerchant }) => {
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  // New item form
  const [itemName, setItemName] = useState('');
  const [itemCategory, setItemCategory] = useState('');
  const [itemPrice, setItemPrice] = useState('');
  const [itemStock, setItemStock] = useState('20');
  const [itemUnit, setItemUnit] = useState('piece');
  const [itemDesc, setItemDesc] = useState('');
  const [isSugarFree, setIsSugarFree] = useState(false);
  const [durationMins, setDurationMins] = useState('60');

  const loadItems = () => {
    setLoading(true);
    ApiClient.getCatalogItems()
      .then((data) => {
        if (Array.isArray(data)) setItems(data);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadItems();
  }, [activeMerchant]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!itemName || !itemCategory || !itemPrice) return;

    await ApiClient.createCatalogItem({
      name: itemName,
      category: itemCategory,
      price: parseFloat(itemPrice),
      stock_quantity: parseInt(itemStock || '0'),
      unit: itemUnit,
      description: itemDesc,
      is_sugar_free: isSugarFree,
      duration_minutes: parseInt(durationMins || '60')
    });

    setShowAddModal(false);
    setItemName('');
    setItemCategory('');
    setItemPrice('');
    setItemDesc('');
    loadItems();
  };

  const handleStockAdjust = async (itemId: string, currentStock: number, delta: number) => {
    const newStock = Math.max(0, currentStock + delta);
    await ApiClient.updateStock(itemId, newStock);
    loadItems();
  };

  const handleDelete = async (itemId: string) => {
    if (confirm('Are you sure you want to remove this record?')) {
      await ApiClient.deleteCatalogItem(itemId);
      loadItems();
    }
  };

  const filteredItems = items.filter((it) => {
    const s = search.toLowerCase();
    return it.name.toLowerCase().includes(s) || it.category.toLowerCase().includes(s);
  });

  const isServiceMerchant = activeMerchant?.business_type === 'salon' || activeMerchant?.business_type === 'dental';

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Package className="w-6 h-6 text-emerald-400" />
            <span>{isServiceMerchant ? 'Services Catalog & Pricing' : 'Products & Live Inventory'}</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Authoritative records referenced by Nexa during customer conversations and order placement.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm shadow-lg shadow-emerald-600/20 transition self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Add {isServiceMerchant ? 'Service' : 'Product'}</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={`Search ${isServiceMerchant ? 'services' : 'products'} or categories...`}
          className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500 placeholder:text-slate-500"
        />
      </div>

      {/* Catalog Table */}
      {loading ? (
        <div className="py-12 flex justify-center text-slate-400">Loading catalog...</div>
      ) : filteredItems.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-800/30 border border-slate-800/60">
          <Package className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-300">No items found</h3>
          <p className="text-sm text-slate-500 mt-1">Add items to make them discoverable by customers on WhatsApp.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-800/40 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <th className="py-3.5 px-6">Name & Description</th>
                <th className="py-3.5 px-6">Category</th>
                <th className="py-3.5 px-6">Price</th>
                {!isServiceMerchant && <th className="py-3.5 px-6">Stock Status</th>}
                {isServiceMerchant && <th className="py-3.5 px-6">Duration</th>}
                <th className="py-3.5 px-6 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-sm">
              {filteredItems.map((item) => (
                <tr key={item.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-4 px-6">
                    <div>
                      <p className="font-semibold text-white">{item.name}</p>
                      {item.description && (
                        <p className="text-xs text-slate-400 mt-0.5 max-w-md line-clamp-1">
                          {item.description}
                        </p>
                      )}
                      {item.is_sugar_free && (
                        <span className="inline-block mt-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Sugar Free
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700/80 text-xs font-medium text-slate-300">
                      <Tag className="w-3 h-3 text-slate-400" />
                      <span>{item.category}</span>
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <span className="font-bold text-white">₹{item.price.toFixed(2)}</span>
                    {item.unit && <span className="text-xs text-slate-400 ml-1">/{item.unit}</span>}
                  </td>

                  {!isServiceMerchant && (
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-3">
                        <span
                          className={`font-mono font-bold text-sm ${
                            (item.stock || 0) > 10 ? 'text-emerald-400' : 'text-amber-400'
                          }`}
                        >
                          {item.stock ?? 0}
                        </span>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleStockAdjust(item.id, item.stock || 0, -5)}
                            className="w-6 h-6 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center font-bold text-xs"
                          >
                            -5
                          </button>
                          <button
                            onClick={() => handleStockAdjust(item.id, item.stock || 0, 10)}
                            className="w-6 h-6 rounded bg-slate-800 hover:bg-slate-700 text-emerald-400 flex items-center justify-center font-bold text-xs"
                          >
                            +10
                          </button>
                        </div>
                      </div>
                    </td>
                  )}

                  {isServiceMerchant && (
                    <td className="py-4 px-6">
                      <span className="inline-flex items-center gap-1 text-xs text-slate-300">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>{item.duration_minutes || 60} mins</span>
                      </span>
                    </td>
                  )}

                  <td className="py-4 px-6 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <CheckCircle className="w-3 h-3" />
                        <span>Active</span>
                      </span>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
                        title="Delete item"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Item Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-1">
              Add {isServiceMerchant ? 'Service' : 'Product'}
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Add authoritative business records for {activeMerchant?.name}.
            </p>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Name</label>
                <input
                  type="text"
                  value={itemName}
                  onChange={(e) => setItemName(e.target.value)}
                  placeholder={isServiceMerchant ? 'e.g. Deep Cleansing Facial' : 'e.g. Organic Almond Butter'}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Category</label>
                  <input
                    type="text"
                    value={itemCategory}
                    onChange={(e) => setItemCategory(e.target.value)}
                    placeholder="e.g. Pantry / Hair Care"
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={itemPrice}
                    onChange={(e) => setItemPrice(e.target.value)}
                    placeholder="0.00"
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                    required
                  />
                </div>
              </div>

              {!isServiceMerchant && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">Stock Quantity</label>
                    <input
                      type="number"
                      value={itemStock}
                      onChange={(e) => setItemStock(e.target.value)}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">Unit</label>
                    <input
                      type="text"
                      value={itemUnit}
                      onChange={(e) => setItemUnit(e.target.value)}
                      placeholder="kg, pack, jar"
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                </div>
              )}

              {isServiceMerchant && (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Duration (Minutes)</label>
                  <input
                    type="number"
                    value={durationMins}
                    onChange={(e) => setDurationMins(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Description</label>
                <textarea
                  value={itemDesc}
                  onChange={(e) => setItemDesc(e.target.value)}
                  rows={2}
                  placeholder="Details, ingredients, or package features..."
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-semibold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition"
                >
                  Save Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
