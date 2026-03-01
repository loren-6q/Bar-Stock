import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Label } from './components/ui/label';
import { useToast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';
import { Copy, Plus, Trash2, Save, CheckCircle, Edit2, Package } from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Categories and Suppliers
const defaultCategories = [
  { value: 'B', label: 'Beer' },
  { value: 'A', label: 'Thai Alcohol' },
  { value: 'I', label: 'Import Alcohol' },
  { value: 'M', label: 'Mixers' },
  { value: 'O', label: 'Bar Supplies' },
  { value: 'Z', label: 'Hostel Supplies' }
];

const defaultSuppliers = [
  'Singha99', 'Makro', 'Local Market', 'zBKK', 'Tesco', 'Big C', 'Vendor', 'Samui', 'Mr DIY', 'Supercheap', 'Lazada', 'Other'
];

const categoryColors = {
  'Beer': 'bg-amber-200 text-amber-900',
  'Thai Alcohol': 'bg-red-200 text-red-900',
  'Import Alcohol': 'bg-pink-200 text-pink-900',
  'Mixers': 'bg-blue-200 text-blue-900',
  'Bar Supplies': 'bg-green-200 text-green-900',
  'Hostel Supplies': 'bg-purple-200 text-purple-900'
};

const supplierColors = {
  'Singha99': 'bg-emerald-600',
  'Makro': 'bg-orange-500',
  'Local Market': 'bg-indigo-500',
  'zBKK': 'bg-purple-600',
  'Tesco': 'bg-blue-500',
  'Big C': 'bg-red-500',
  'Vendor': 'bg-gray-600',
  'Samui': 'bg-cyan-500',
  'Mr DIY': 'bg-yellow-600',
  'Supercheap': 'bg-lime-600',
  'Lazada': 'bg-orange-600',
  'Other': 'bg-gray-500'
};

function StockManager() {
  const [activeTab, setActiveTab] = useState('count');
  const [items, setItems] = useState([]);
  const [stockCounts, setStockCounts] = useState({});
  const [localCounts, setLocalCounts] = useState({}); // Local state for inputs
  const [orderQtys, setOrderQtys] = useState({});
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [caseMode, setCaseMode] = useState({}); // Track case input mode per item
  const [caseCounts, setCaseCounts] = useState({}); // cases + singles input
  
  // Dialogs
  const [copyDialogOpen, setCopyDialogOpen] = useState(false);
  const [copyText, setCopyText] = useState('');
  const [confirmPurchaseOpen, setConfirmPurchaseOpen] = useState(false);
  const [currentOrder, setCurrentOrder] = useState(null);
  const [viewSessionOpen, setViewSessionOpen] = useState(false);
  const [viewingSession, setViewingSession] = useState(null);
  const [sessionCounts, setSessionCounts] = useState([]);
  
  // Manage tab filter and editing state
  const [manageFilter, setManageFilter] = useState('');
  const [editingCell, setEditingCell] = useState(null); // {id, field}
  const [editValue, setEditValue] = useState('');
  
  const { toast } = useToast();

  // Load data on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [itemsRes, countsRes, sessionsRes] = await Promise.all([
        axios.get(`${API}/items`),
        axios.get(`${API}/stock-counts`),
        axios.get(`${API}/stock-sessions`)
      ]);
      
      setItems(itemsRes.data);
      
      // Convert counts array to map
      const countsMap = {};
      const localMap = {};
      countsRes.data.forEach(count => {
        countsMap[count.item_id] = count;
        localMap[count.item_id] = {
          main_bar: count.main_bar || 0,
          beer_bar: count.beer_bar || 0,
          lobby: count.lobby || 0,
          storage_room: count.storage_room || 0
        };
      });
      setStockCounts(countsMap);
      setLocalCounts(localMap);
      setSessions(sessionsRes.data);
      
      // Load saved order quantities and case modes from localStorage
      try {
        const savedOrders = localStorage.getItem('orderQtys');
        if (savedOrders) setOrderQtys(JSON.parse(savedOrders));
        const savedCaseModes = localStorage.getItem('caseModes');
        if (savedCaseModes) setCaseMode(JSON.parse(savedCaseModes));
      } catch (e) {}
    } catch (error) {
      console.error('Error loading data:', error);
      toast({
        title: "Connection Error",
        description: "Could not load data. Please refresh.",
        variant: "destructive",
      });
    }
    setLoading(false);
  };

  // Update local count (immediate, no API call)
  const updateLocalCount = (itemId, location, value) => {
    setLocalCounts(prev => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        [location]: value
      }
    }));
  };

  // Save count to server (on blur)
  const saveCount = async (itemId, location) => {
    const value = parseInt(localCounts[itemId]?.[location]) || 0;
    try {
      await axios.put(`${API}/stock-counts/${itemId}`, { [location]: value });
      
      // Update stockCounts state
      setStockCounts(prev => {
        const current = prev[itemId] || {};
        return {
          ...prev,
          [itemId]: {
            ...current,
            [location]: value,
            total_count: (location === 'main_bar' ? value : (current.main_bar || 0)) +
                         (location === 'beer_bar' ? value : (current.beer_bar || 0)) +
                         (location === 'lobby' ? value : (current.lobby || 0)) +
                         (location === 'storage_room' ? value : (current.storage_room || 0))
          }
        };
      });
    } catch (error) {
      console.error('Error saving count:', error);
    }
  };

  // Toggle case mode for an item
  const toggleCaseMode = (itemId) => {
    const newMode = { ...caseMode, [itemId]: !caseMode[itemId] };
    setCaseMode(newMode);
    localStorage.setItem('caseModes', JSON.stringify(newMode));
  };

  // Update case/singles count
  const updateCaseCount = (itemId, location, field, value) => {
    setCaseCounts(prev => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        [location]: {
          ...prev[itemId]?.[location],
          [field]: value
        }
      }
    }));
  };

  // Calculate total from cases + singles and save
  const saveCaseCount = async (itemId, location, unitsPerCase) => {
    const caseData = caseCounts[itemId]?.[location] || {};
    const cases = parseInt(caseData.cases) || 0;
    const singles = parseInt(caseData.singles) || 0;
    const total = (cases * unitsPerCase) + singles;
    
    // Update local and save
    updateLocalCount(itemId, location, total);
    
    try {
      await axios.put(`${API}/stock-counts/${itemId}`, { [location]: total });
      setStockCounts(prev => ({
        ...prev,
        [itemId]: { ...prev[itemId], [location]: total }
      }));
    } catch (error) {
      console.error('Error saving count:', error);
    }
  };

  // Save session
  const saveSession = async () => {
    const sessionName = `Stock Count ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
    try {
      const sessionRes = await axios.post(`${API}/stock-sessions`, {
        session_name: sessionName,
        session_type: 'full_count'
      });
      
      await axios.post(`${API}/stock-sessions/${sessionRes.data.id}/save-counts`);
      
      toast({
        title: "Session Saved!",
        description: sessionName,
      });
      
      loadData();
      setActiveTab('inventory');
    } catch (error) {
      console.error('Error saving session:', error);
      toast({
        title: "Error",
        description: "Could not save session",
        variant: "destructive",
      });
    }
  };

  // Get total stock for an item
  const getTotalStock = (itemId) => {
    const count = stockCounts[itemId];
    if (!count) return 0;
    return (count.main_bar || 0) + (count.beer_bar || 0) + (count.lobby || 0) + (count.storage_room || 0);
  };

  // Get cases equivalent
  const getCases = (units, unitsPerCase) => {
    if (unitsPerCase <= 1) return null;
    return (units / unitsPerCase).toFixed(1);
  };

  // Get target stock (use target_stock or fall back to max_stock for old data)
  const getTarget = (item) => item.target_stock || item.max_stock || 0;

  // Get suggested order quantity
  const getSuggestedOrder = (item) => {
    const have = getTotalStock(item.id);
    const target = getTarget(item);
    const need = Math.max(0, target - have);
    if (item.units_per_case > 1 && item.bought_by_case) {
      return Math.ceil(need / item.units_per_case);
    }
    return need;
  };

  // Update order quantity
  const updateOrderQty = (itemId, value) => {
    const newQtys = { ...orderQtys, [itemId]: value };
    setOrderQtys(newQtys);
    localStorage.setItem('orderQtys', JSON.stringify(newQtys));
  };

  // Generate orders by supplier
  const generateOrders = () => {
    const orders = {};
    
    items.forEach(item => {
      const suggested = getSuggestedOrder(item);
      const qty = orderQtys[item.id] !== undefined ? parseInt(orderQtys[item.id]) || 0 : suggested;
      if (qty > 0) {
        const supplier = item.primary_supplier || 'Other';
        if (!orders[supplier]) orders[supplier] = [];
        const isCase = item.units_per_case > 1 && item.bought_by_case;
        orders[supplier].push({
          ...item,
          orderQty: qty,
          orderUnits: isCase ? qty * item.units_per_case : qty,
          isCase,
          cost: isCase 
            ? qty * (parseFloat(item.cost_per_case) || parseFloat(item.cost_per_unit) * item.units_per_case)
            : qty * parseFloat(item.cost_per_unit)
        });
      }
    });
    
    return orders;
  };

  // View session details
  const viewSession = async (session) => {
    try {
      const response = await axios.get(`${API}/stock-sessions/${session.id}/counts`);
      setSessionCounts(response.data);
      setViewingSession(session);
      setViewSessionOpen(true);
    } catch (error) {
      console.error('Error loading session:', error);
      toast({
        title: "Error loading session",
        description: "Could not load session data",
        variant: "destructive",
      });
    }
  };

  // Copy order list
  const copyOrderList = (supplier, orderItems) => {
    let text = `Order for ${supplier}:\n\n`;
    let total = 0;
    
    orderItems.forEach(item => {
      const unit = item.isCase ? 'cases' : 'units';
      text += `• ${item.name}: ${item.orderQty} ${unit}\n`;
      total += item.cost;
    });
    
    text += `\nTotal: ฿${total.toFixed(0)}`;
    
    setCopyText(text);
    setCopyDialogOpen(true);
  };

  // Confirm purchase - opens dialog with editable quantities
  const startConfirmPurchase = (supplier, orderItems) => {
    setCurrentOrder({
      supplier,
      items: orderItems.map(item => ({
        ...item,
        actualQty: item.orderQty,
        actualCost: item.cost
      }))
    });
    setConfirmPurchaseOpen(true);
  };

  // Save confirmed purchase
  const savePurchase = async () => {
    if (!currentOrder) return;
    
    try {
      await axios.post(`${API}/orders`, {
        id: Date.now().toString(),
        supplier: currentOrder.supplier,
        status: 'completed',
        completed_at: new Date().toISOString(),
        items: currentOrder.items
      });
      
      toast({ title: "Purchase recorded!", description: `Order from ${currentOrder.supplier} saved.` });
      setConfirmPurchaseOpen(false);
      setCurrentOrder(null);
      
      // Clear order quantities for this supplier
      const newQtys = { ...orderQtys };
      currentOrder.items.forEach(item => delete newQtys[item.id]);
      setOrderQtys(newQtys);
      localStorage.setItem('orderQtys', JSON.stringify(newQtys));
    } catch (error) {
      toast({ title: "Error saving purchase", variant: "destructive" });
    }
  };

  // Save item (inline edit)
  const saveItem = async (itemId, updates) => {
    try {
      const item = items.find(i => i.id === itemId);
      const payload = { ...item, ...updates };
      
      // Auto-calculate costs
      if (updates.cost_per_unit !== undefined && payload.units_per_case > 1) {
        payload.cost_per_case = parseFloat(updates.cost_per_unit) * payload.units_per_case;
      } else if (updates.cost_per_case !== undefined && payload.units_per_case > 1) {
        payload.cost_per_unit = parseFloat(updates.cost_per_case) / payload.units_per_case;
      }
      
      await axios.put(`${API}/items/${itemId}`, payload);
      
      // Update local state
      setItems(prev => prev.map(i => i.id === itemId ? { ...i, ...payload } : i));
    } catch (error) {
      console.error('Error saving item:', error);
      toast({ title: "Error saving", variant: "destructive" });
    }
  };

  // Add new item
  const addItem = async () => {
    const newItem = {
      name: 'New Item',
      category: 'O',
      category_name: 'Bar Supplies',
      sub_category: '',
      units_per_case: 1,
      target_stock: 0,
      primary_supplier: 'Makro',
      cost_per_unit: 0,
      cost_per_case: 0,
      bought_by_case: false
    };
    
    try {
      const res = await axios.post(`${API}/items`, newItem);
      setItems(prev => [...prev, res.data]);
      toast({ title: "Item added" });
    } catch (error) {
      toast({ title: "Error adding item", variant: "destructive" });
    }
  };

  // Duplicate item
  const duplicateItem = async (item) => {
    const newItem = {
      ...item,
      name: `${item.name} (copy)`
    };
    delete newItem.id;
    
    try {
      const res = await axios.post(`${API}/items`, newItem);
      setItems(prev => [...prev, res.data]);
      toast({ title: "Item duplicated" });
    } catch (error) {
      toast({ title: "Error duplicating", variant: "destructive" });
    }
  };

  // Delete item
  const deleteItem = async (itemId) => {
    if (!window.confirm('Delete this item?')) return;
    try {
      await axios.delete(`${API}/items/${itemId}`);
      setItems(prev => prev.filter(i => i.id !== itemId));
      toast({ title: "Item deleted" });
    } catch (error) {
      toast({ title: "Error deleting", variant: "destructive" });
    }
  };

  // Group items by category and sub-category for display
  const groupItems = (itemsList) => {
    const groups = {};
    itemsList.forEach(item => {
      const cat = item.category_name || 'Other';
      const sub = item.sub_category || '';
      const key = sub ? `${cat} - ${sub}` : cat;
      if (!groups[key]) groups[key] = { category: cat, subCategory: sub, items: [] };
      groups[key].items.push(item);
    });
    
    // Sort groups by category then sub-category
    const categoryOrder = ['Beer', 'Thai Alcohol', 'Import Alcohol', 'Mixers', 'Bar Supplies', 'Hostel Supplies'];
    const sortedKeys = Object.keys(groups).sort((a, b) => {
      const catA = groups[a].category;
      const catB = groups[b].category;
      const idxA = categoryOrder.indexOf(catA);
      const idxB = categoryOrder.indexOf(catB);
      if (idxA !== idxB) return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB);
      return a.localeCompare(b);
    });
    
    // Sort items within groups alphabetically
    sortedKeys.forEach(key => {
      groups[key].items.sort((a, b) => a.name.localeCompare(b.name));
    });
    
    return { groups, sortedKeys };
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  const orders = generateOrders();
  const { groups, sortedKeys } = groupItems(items);

  // Filter items for manage tab
  const filteredItems = manageFilter 
    ? items.filter(i => 
        i.name.toLowerCase().includes(manageFilter.toLowerCase()) ||
        i.category_name?.toLowerCase().includes(manageFilter.toLowerCase()) ||
        i.sub_category?.toLowerCase().includes(manageFilter.toLowerCase()) ||
        i.primary_supplier?.toLowerCase().includes(manageFilter.toLowerCase())
      )
    : items;
  
  const { groups: manageGroups, sortedKeys: manageSortedKeys } = groupItems(filteredItems);

  // Inline cell edit helpers (prevents re-sort while typing)
  const startCellEdit = (itemId, field, value) => {
    setEditingCell({ id: itemId, field });
    setEditValue(value != null ? String(value) : '');
  };
  const commitCellEdit = (itemId, field, transform) => {
    const val = transform ? transform(editValue) : editValue;
    saveItem(itemId, { [field]: val });
    setEditingCell(null);
  };
  const getEditOrVal = (itemId, field, fallback) =>
    editingCell?.id === itemId && editingCell?.field === field ? editValue : fallback;

  // Pre-compute group display flags for manage tab
  const manageDisplayGroups = manageSortedKeys.map((key, idx) => ({
    key,
    group: manageGroups[key],
    showCatHeader: idx === 0 || manageGroups[key].category !== manageGroups[manageSortedKeys[idx - 1]].category
  }));

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 pb-20">
      <div className="container mx-auto px-2 sm:px-4 py-4 max-w-6xl">
        {/* Header */}
        <div className="mb-4 text-center">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Bar Stock Manager</h1>
          <p className="text-gray-600 text-xs sm:text-sm">{items.length} items</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-4">
            <TabsTrigger value="count" className="text-xs sm:text-sm">Count</TabsTrigger>
            <TabsTrigger value="inventory" className="text-xs sm:text-sm">Inventory</TabsTrigger>
            <TabsTrigger value="orders" className="text-xs sm:text-sm">Orders</TabsTrigger>
            <TabsTrigger value="manage" className="text-xs sm:text-sm">Manage</TabsTrigger>
            <TabsTrigger value="accounting" className="text-xs sm:text-sm">Accounting</TabsTrigger>
          </TabsList>

          {/* ==================== COUNT TAB ==================== */}
          <TabsContent value="count" className="space-y-3">
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="p-3 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-blue-900 text-sm">Stock Count</h3>
                  <p className="text-xs text-blue-700">Enter counts by location</p>
                </div>
                <Button onClick={saveSession} size="sm">
                  <Save className="w-4 h-4 mr-1" />
                  Save & Continue
                </Button>
              </CardContent>
            </Card>

            {sortedKeys.map(groupKey => (
              <div key={groupKey} className="space-y-1">
                <div className={`sticky top-0 z-10 px-2 py-1 rounded text-xs font-semibold ${categoryColors[groups[groupKey].category] || 'bg-gray-200'}`}>
                  {groupKey} ({groups[groupKey].items.length})
                </div>
                
                {groups[groupKey].items.map(item => {
                  const showCaseInput = caseMode[item.id] && item.units_per_case > 1;
                  const localCount = localCounts[item.id] || {};
                  
                  return (
                    <Card key={item.id} className="shadow-sm">
                      {/* Item Header */}
                      <div className="px-2 py-1.5 border-b flex items-center justify-between bg-gray-50">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <span className="font-medium text-sm truncate">{item.name}</span>
                          {item.units_per_case > 1 && (
                            <Badge variant="outline" className="text-xs shrink-0">{item.units_per_case}/case</Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          {item.units_per_case > 1 && (
                            <Button
                              variant={showCaseInput ? "default" : "outline"}
                              size="sm"
                              onClick={() => toggleCaseMode(item.id)}
                              className="h-6 px-2 text-xs"
                            >
                              <Package className="w-3 h-3 mr-1" />
                              {showCaseInput ? 'Cases' : 'Units'}
                            </Button>
                          )}
                          <div className="text-lg font-bold text-blue-600 min-w-[40px] text-right">
                            {getTotalStock(item.id)}
                          </div>
                        </div>
                      </div>
                      
                      {/* Location Inputs */}
                      <div className="p-1.5 grid grid-cols-2 sm:grid-cols-4 gap-1">
                        {[
                          { key: 'main_bar', label: 'Bar', bg: 'bg-orange-200' },
                          { key: 'beer_bar', label: 'Beer', bg: 'bg-yellow-200' },
                          { key: 'lobby', label: 'Lobby', bg: 'bg-blue-200' },
                          { key: 'storage_room', label: 'Storage', bg: 'bg-green-200' }
                        ].map(loc => (
                          <div key={loc.key} className={`${loc.bg} rounded px-2 py-1`}>
                            <div className="text-xs font-medium mb-1">{loc.label}</div>
                            
                            {showCaseInput ? (
                              // Case + Singles mode
                              <div className="flex gap-1">
                                <div className="flex-1">
                                  <input
                                    type="number"
                                    inputMode="numeric"
                                    min="0"
                                    value={caseCounts[item.id]?.[loc.key]?.cases ?? ''}
                                    onChange={(e) => updateCaseCount(item.id, loc.key, 'cases', e.target.value)}
                                    onBlur={() => saveCaseCount(item.id, loc.key, item.units_per_case)}
                                    className="w-full h-7 text-center font-bold text-sm bg-white rounded border px-1"
                                    placeholder="0"
                                  />
                                  <div className="text-[10px] text-center text-gray-600">📦</div>
                                </div>
                                <div className="flex-1">
                                  <input
                                    type="number"
                                    inputMode="numeric"
                                    min="0"
                                    value={caseCounts[item.id]?.[loc.key]?.singles ?? ''}
                                    onChange={(e) => updateCaseCount(item.id, loc.key, 'singles', e.target.value)}
                                    onBlur={() => saveCaseCount(item.id, loc.key, item.units_per_case)}
                                    className="w-full h-7 text-center font-bold text-sm bg-white rounded border px-1"
                                    placeholder="0"
                                  />
                                  <div className="text-[10px] text-center text-gray-600">1️⃣</div>
                                </div>
                              </div>
                            ) : (
                              // Simple units mode
                              <input
                                type="number"
                                inputMode="numeric"
                                min="0"
                                value={localCount[loc.key] ?? ''}
                                onChange={(e) => updateLocalCount(item.id, loc.key, e.target.value)}
                                onBlur={() => saveCount(item.id, loc.key)}
                                className="w-full h-7 text-center font-bold text-sm bg-white rounded border"
                                placeholder="0"
                              />
                            )}
                          </div>
                        ))}
                      </div>
                    </Card>
                  );
                })}
              </div>
            ))}
          </TabsContent>

          {/* ==================== INVENTORY TAB ==================== */}
          <TabsContent value="inventory" className="space-y-3">
            <Card className="bg-green-50 border-green-200">
              <CardContent className="p-3">
                <h3 className="font-semibold text-green-900 text-sm">Full Inventory</h3>
                <p className="text-xs text-green-700">Review stock and set order quantities</p>
              </CardContent>
            </Card>

            <div className="overflow-x-auto bg-white rounded-lg shadow">
              <table className="w-full text-xs sm:text-sm">
                <thead className="bg-gray-100 sticky top-0">
                  <tr>
                    <th className="text-left p-2 font-semibold">Item</th>
                    <th className="text-center p-2 font-semibold">Have</th>
                    <th className="text-center p-2 font-semibold">Cases</th>
                    <th className="text-center p-2 font-semibold">Target</th>
                    <th className="text-center p-2 font-semibold">Need</th>
                    <th className="text-center p-2 font-semibold bg-blue-100">Order</th>
                    <th className="text-left p-2 font-semibold">Vendor</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedKeys.map(groupKey => (
                    <React.Fragment key={groupKey}>
                      <tr className={categoryColors[groups[groupKey].category] || 'bg-gray-200'}>
                        <td colSpan={7} className="p-1 font-semibold text-xs">{groupKey}</td>
                      </tr>
                      {groups[groupKey].items.map(item => {
                        const have = getTotalStock(item.id);
                        const target = getTarget(item);
                        const need = Math.max(0, target - have);
                        const cases = getCases(have, item.units_per_case);
                        const suggested = getSuggestedOrder(item);
                        const orderQty = orderQtys[item.id] ?? suggested;
                        const isCase = item.units_per_case > 1 && item.bought_by_case;
                        
                        return (
                          <tr key={item.id} className="border-b hover:bg-gray-50">
                            <td className="p-2">{item.name}</td>
                            <td className={`p-2 text-center ${have < target * 0.25 ? 'text-red-600 font-bold' : ''}`}>{have}</td>
                            <td className="p-2 text-center text-gray-500">{cases || '-'}</td>
                            <td className="p-2 text-center">{target || '-'}</td>
                            <td className="p-2 text-center">{need > 0 ? need : '-'}</td>
                            <td className="p-2 text-center bg-blue-50">
                              <input
                                type="number"
                                min="0"
                                value={orderQty}
                                onChange={(e) => updateOrderQty(item.id, e.target.value)}
                                className="w-14 h-6 text-center font-bold text-sm border rounded mx-auto block"
                              />
                              <div className="text-[10px] text-gray-500">{isCase ? 'cases' : 'units'}</div>
                            </td>
                            <td className="p-2">
                              <Badge className={`${supplierColors[item.primary_supplier] || 'bg-gray-500'} text-white text-xs`}>
                                {item.primary_supplier}
                              </Badge>
                            </td>
                          </tr>
                        );
                      })}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>

            <Button onClick={() => setActiveTab('orders')} className="w-full">
              View Orders →
            </Button>
          </TabsContent>

          {/* ==================== ORDERS TAB ==================== */}
          <TabsContent value="orders" className="space-y-3">
            {Object.keys(orders).length === 0 ? (
              <Card className="text-center py-8">
                <CardContent>
                  <p className="text-gray-500">No orders to place. Set quantities in Inventory tab.</p>
                </CardContent>
              </Card>
            ) : (
              Object.entries(orders).map(([supplier, orderItems]) => {
                const total = orderItems.reduce((sum, item) => sum + item.cost, 0);
                
                return (
                  <Card key={supplier}>
                    <CardHeader className={`${supplierColors[supplier] || 'bg-gray-500'} text-white rounded-t-lg py-2 px-3`}>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">{supplier}</CardTitle>
                        <div className="flex items-center gap-2">
                          <Badge className="bg-white/20 text-white">฿{total.toFixed(0)}</Badge>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => copyOrderList(supplier, orderItems)}
                            className="h-7 text-xs"
                          >
                            <Copy className="w-3 h-3 mr-1" /> Copy
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => startConfirmPurchase(supplier, orderItems)}
                            className="h-7 text-xs bg-white text-gray-900 hover:bg-gray-100"
                          >
                            <CheckCircle className="w-3 h-3 mr-1" /> Confirm
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="divide-y">
                        {orderItems.map((item, idx) => (
                          <div key={idx} className="px-3 py-2 flex justify-between items-center">
                            <div>
                              <span className="font-medium text-sm">{item.name}</span>
                              {item.isCase && (
                                <span className="text-xs text-gray-500 ml-2">({item.orderUnits} units)</span>
                              )}
                            </div>
                            <div className="text-right">
                              <span className="font-bold">{item.orderQty} {item.isCase ? 'cases' : 'units'}</span>
                              <span className="text-xs text-gray-500 ml-2">฿{item.cost.toFixed(0)}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                );
              })
            )}
          </TabsContent>

          {/* ==================== MANAGE TAB (Spreadsheet Style) ==================== */}
          <TabsContent value="manage" className="space-y-3">
            <div className="flex items-center gap-2 mb-2">
              <Input
                placeholder="Filter items..."
                value={manageFilter}
                onChange={(e) => setManageFilter(e.target.value)}
                className="flex-1 h-8 text-sm"
              />
              <Button size="sm" onClick={addItem}>
                <Plus className="w-4 h-4 mr-1" /> Add
              </Button>
            </div>

            <div className="overflow-x-auto bg-white rounded-lg shadow">
              <table className="w-full text-xs">
                <thead className="bg-gray-100 sticky top-0">
                  <tr>
                    <th className="text-left p-1.5 font-semibold min-w-[150px]">Name</th>
                    <th className="text-left p-1.5 font-semibold min-w-[100px]">Category</th>
                    <th className="text-left p-1.5 font-semibold min-w-[80px]">Sub-Cat</th>
                    <th className="text-left p-1.5 font-semibold min-w-[80px]">Vendor</th>
                    <th className="text-center p-1.5 font-semibold w-16">#/Case</th>
                    <th className="text-center p-1.5 font-semibold w-20">฿/Unit</th>
                    <th className="text-center p-1.5 font-semibold w-20">฿/Case</th>
                    <th className="text-center p-1.5 font-semibold w-16">Target</th>
                    <th className="text-center p-1.5 font-semibold w-12">Case?</th>
                    <th className="text-center p-1.5 font-semibold w-16">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {manageSortedKeys.map(groupKey => (
                    <React.Fragment key={groupKey}>
                      <tr className={categoryColors[manageGroups[groupKey].category] || 'bg-gray-200'}>
                        <td colSpan={10} className="p-1 font-semibold text-xs">{groupKey}</td>
                      </tr>
                      {manageGroups[groupKey].items.map(item => (
                        <tr key={item.id} className="border-b hover:bg-gray-50">
                          <td className="p-1">
                            <input
                              type="text"
                              value={item.name}
                              onChange={(e) => setItems(prev => prev.map(i => i.id === item.id ? {...i, name: e.target.value} : i))}
                              onBlur={(e) => saveItem(item.id, { name: e.target.value })}
                              className="w-full h-6 px-1 text-xs border rounded"
                            />
                          </td>
                          <td className="p-1">
                            <select
                              value={item.category_name}
                              onChange={(e) => {
                                const cat = defaultCategories.find(c => c.label === e.target.value);
                                saveItem(item.id, { category: cat?.value || 'O', category_name: e.target.value });
                              }}
                              className="w-full h-6 px-1 text-xs border rounded"
                            >
                              {defaultCategories.map(c => (
                                <option key={c.label} value={c.label}>{c.label}</option>
                              ))}
                            </select>
                          </td>
                          <td className="p-1">
                            <input
                              type="text"
                              value={item.sub_category || ''}
                              onChange={(e) => setItems(prev => prev.map(i => i.id === item.id ? {...i, sub_category: e.target.value} : i))}
                              onBlur={(e) => saveItem(item.id, { sub_category: e.target.value })}
                              className="w-full h-6 px-1 text-xs border rounded"
                              placeholder="e.g. Rum"
                            />
                          </td>
                          <td className="p-1">
                            <select
                              value={item.primary_supplier}
                              onChange={(e) => saveItem(item.id, { primary_supplier: e.target.value })}
                              className="w-full h-6 px-1 text-xs border rounded"
                            >
                              {defaultSuppliers.map(s => (
                                <option key={s} value={s}>{s}</option>
                              ))}
                            </select>
                          </td>
                          <td className="p-1">
                            <input
                              type="number"
                              min="1"
                              value={item.units_per_case}
                              onChange={(e) => setItems(prev => prev.map(i => i.id === item.id ? {...i, units_per_case: parseInt(e.target.value) || 1} : i))}
                              onBlur={(e) => saveItem(item.id, { units_per_case: parseInt(e.target.value) || 1 })}
                              className="w-full h-6 px-1 text-xs border rounded text-center"
                            />
                          </td>
                          <td className="p-1">
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={item.cost_per_unit || ''}
                              onChange={(e) => setItems(prev => prev.map(i => i.id === item.id ? {...i, cost_per_unit: e.target.value} : i))}
                              onBlur={(e) => saveItem(item.id, { cost_per_unit: parseFloat(e.target.value) || 0 })}
                              className="w-full h-6 px-1 text-xs border rounded text-center"
                            />
                          </td>
                          <td className="p-1">
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={item.cost_per_case || ''}
                              onChange={(e) => setItems(prev => prev.map(i => i.id === item.id ? {...i, cost_per_case: e.target.value} : i))}
                              onBlur={(e) => saveItem(item.id, { cost_per_case: parseFloat(e.target.value) || 0 })}
                              className="w-full h-6 px-1 text-xs border rounded text-center"
                            />
                          </td>
                          <td className="p-1">
                            <input
                              type="number"
                              min="0"
                              value={item.target_stock || item.max_stock || ''}
                              onChange={(e) => setItems(prev => prev.map(i => i.id === item.id ? {...i, target_stock: e.target.value} : i))}
                              onBlur={(e) => saveItem(item.id, { target_stock: parseInt(e.target.value) || 0 })}
                              className="w-full h-6 px-1 text-xs border rounded text-center"
                            />
                          </td>
                          <td className="p-1 text-center">
                            <input
                              type="checkbox"
                              checked={item.bought_by_case || false}
                              onChange={(e) => saveItem(item.id, { bought_by_case: e.target.checked })}
                              className="w-4 h-4"
                            />
                          </td>
                          <td className="p-1 text-center">
                            <div className="flex gap-1 justify-center">
                              <button
                                onClick={() => duplicateItem(item)}
                                className="p-1 hover:bg-gray-200 rounded"
                                title="Duplicate"
                              >
                                <Copy className="w-3 h-3" />
                              </button>
                              <button
                                onClick={() => deleteItem(item.id)}
                                className="p-1 hover:bg-red-100 rounded text-red-600"
                                title="Delete"
                              >
                                <Trash2 className="w-3 h-3" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </TabsContent>

          {/* ==================== ACCOUNTING TAB ==================== */}
          <TabsContent value="accounting" className="space-y-3">
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-base">📋 Saved Stock Counts</CardTitle>
                <p className="text-xs text-gray-500">Click a session to view full inventory at that time</p>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y max-h-[50vh] overflow-y-auto">
                  {sessions.length === 0 ? (
                    <p className="text-center text-gray-500 py-8 text-sm">No saved sessions yet. Save a count from the Count tab.</p>
                  ) : (
                    sessions.map(session => (
                      <button
                        key={session.id}
                        onClick={() => viewSession(session)}
                        className="w-full text-left px-3 py-3 hover:bg-blue-50 transition-colors flex items-center justify-between"
                      >
                        <div>
                          <div className="font-medium text-sm">{session.session_name}</div>
                          <div className="text-xs text-gray-500">
                            {new Date(session.session_date).toLocaleString()}
                          </div>
                        </div>
                        <span className="text-blue-600 text-sm">View →</span>
                      </button>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-base">Usage Analysis</CardTitle>
                <p className="text-xs text-gray-500">Coming soon</p>
              </CardHeader>
              <CardContent>
                <p className="text-center text-gray-400 py-4 text-sm">
                  Opening Stock + Purchases - Closing Stock = Usage<br/>
                  Usage × Cost = Expense | Usage × Sale Price = Revenue
                </p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* ==================== DIALOGS ==================== */}
        
        {/* Copy Dialog */}
        <Dialog open={copyDialogOpen} onOpenChange={setCopyDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Copy Order</DialogTitle>
            </DialogHeader>
            <pre className="bg-gray-100 p-3 rounded text-sm whitespace-pre-wrap">{copyText}</pre>
            <Button onClick={() => {
              navigator.clipboard.writeText(copyText);
              toast({ title: "Copied!" });
              setCopyDialogOpen(false);
            }}>
              <Copy className="w-4 h-4 mr-2" /> Copy to Clipboard
            </Button>
          </DialogContent>
        </Dialog>

        {/* Confirm Purchase Dialog */}
        <Dialog open={confirmPurchaseOpen} onOpenChange={setConfirmPurchaseOpen}>
          <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Confirm Purchase: {currentOrder?.supplier}</DialogTitle>
            </DialogHeader>
            
            {currentOrder && (
              <div className="space-y-3">
                <p className="text-sm text-gray-600">Adjust quantities if actual differs from ordered:</p>
                
                <div className="space-y-2">
                  {currentOrder.items.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <div className="flex-1 min-w-0">
                        <span className="font-medium text-sm truncate block">{item.name}</span>
                        <span className="text-xs text-gray-500">Ordered: {item.orderQty}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs">Got:</span>
                        <input
                          type="number"
                          min="0"
                          value={item.actualQty}
                          onChange={(e) => {
                            const val = parseInt(e.target.value) || 0;
                            const cost = item.isCase 
                              ? val * (parseFloat(item.cost_per_case) || parseFloat(item.cost_per_unit) * item.units_per_case)
                              : val * parseFloat(item.cost_per_unit);
                            setCurrentOrder(prev => ({
                              ...prev,
                              items: prev.items.map((it, i) => i === idx ? {...it, actualQty: val, actualCost: cost} : it)
                            }));
                          }}
                          className="w-14 h-7 text-center border rounded"
                        />
                        <span className="text-xs text-gray-500">
                          ฿{currentOrder.items[idx].actualCost?.toFixed(0)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="flex items-center justify-between pt-2 border-t">
                  <span className="font-bold">
                    Total: ฿{currentOrder.items.reduce((sum, it) => sum + (it.actualCost || 0), 0).toFixed(0)}
                  </span>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setConfirmPurchaseOpen(false)}>Cancel</Button>
                    <Button onClick={savePurchase}>
                      <CheckCircle className="w-4 h-4 mr-1" /> Save Purchase
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* View Session Dialog */}
        <Dialog open={viewSessionOpen} onOpenChange={setViewSessionOpen}>
          <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>📋 {viewingSession?.session_name}</DialogTitle>
              <p className="text-sm text-gray-500">
                {viewingSession && new Date(viewingSession.session_date).toLocaleString()}
              </p>
            </DialogHeader>
            
            {sessionCounts.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No count data found for this session.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-100 sticky top-0">
                    <tr>
                      <th className="text-left p-2">Item</th>
                      <th className="text-center p-2 bg-orange-100">Bar</th>
                      <th className="text-center p-2 bg-yellow-100">Beer</th>
                      <th className="text-center p-2 bg-blue-100">Lobby</th>
                      <th className="text-center p-2 bg-green-100">Storage</th>
                      <th className="text-center p-2 bg-blue-200 font-bold">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(() => {
                      // Map item IDs to names
                      const itemMap = {};
                      items.forEach(item => { itemMap[item.id] = item; });
                      
                      // Group by category
                      const grouped = {};
                      sessionCounts.forEach(count => {
                        const item = itemMap[count.item_id];
                        if (!item) return;
                        const cat = item.category_name || 'Other';
                        if (!grouped[cat]) grouped[cat] = [];
                        grouped[cat].push({ ...count, item });
                      });
                      
                      const categoryOrder = ['Beer', 'Thai Alcohol', 'Import Alcohol', 'Mixers', 'Bar Supplies', 'Hostel Supplies'];
                      const sortedCats = Object.keys(grouped).sort((a, b) => {
                        const idxA = categoryOrder.indexOf(a);
                        const idxB = categoryOrder.indexOf(b);
                        return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB);
                      });
                      
                      return sortedCats.map(cat => (
                        <React.Fragment key={cat}>
                          <tr className={categoryColors[cat] || 'bg-gray-200'}>
                            <td colSpan={6} className="p-1 font-semibold text-xs">{cat}</td>
                          </tr>
                          {grouped[cat]
                            .sort((a, b) => a.item.name.localeCompare(b.item.name))
                            .map(count => (
                              <tr key={count.item_id} className="border-b hover:bg-gray-50">
                                <td className="p-2">{count.item.name}</td>
                                <td className="p-2 text-center bg-orange-50">{count.main_bar || 0}</td>
                                <td className="p-2 text-center bg-yellow-50">{count.beer_bar || 0}</td>
                                <td className="p-2 text-center bg-blue-50">{count.lobby || 0}</td>
                                <td className="p-2 text-center bg-green-50">{count.storage_room || 0}</td>
                                <td className="p-2 text-center font-bold bg-blue-100">{count.total_count || 0}</td>
                              </tr>
                            ))}
                        </React.Fragment>
                      ));
                    })()}
                  </tbody>
                </table>
              </div>
            )}
            
            <div className="flex justify-between items-center pt-2 border-t">
              <span className="text-sm text-gray-500">{sessionCounts.length} items counted</span>
              <Button variant="outline" onClick={() => setViewSessionOpen(false)}>Close</Button>
            </div>
          </DialogContent>
        </Dialog>

        <Toaster />
      </div>
    </div>
  );
}

function App() {
  return <StockManager />;
}

export default App;
