import React, { useState, useEffect } from 'react';
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
import { Copy, Plus, Trash2, Save, CheckCircle } from 'lucide-react';
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
  const [orderQtys, setOrderQtys] = useState({});
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Dialogs
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [copyDialogOpen, setCopyDialogOpen] = useState(false);
  const [copyText, setCopyText] = useState('');
  
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
      countsRes.data.forEach(count => {
        countsMap[count.item_id] = count;
      });
      setStockCounts(countsMap);
      setSessions(sessionsRes.data);
      
      // Load saved order quantities from localStorage
      const savedOrders = localStorage.getItem('orderQtys');
      if (savedOrders) {
        setOrderQtys(JSON.parse(savedOrders));
      }
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

  // Update stock count
  const updateCount = async (itemId, location, value) => {
    const numValue = parseInt(value) || 0;
    try {
      await axios.put(`${API}/stock-counts/${itemId}`, { [location]: numValue });
      
      // Update local state
      setStockCounts(prev => ({
        ...prev,
        [itemId]: {
          ...prev[itemId],
          [location]: numValue,
          total_count: (location === 'main_bar' ? numValue : (prev[itemId]?.main_bar || 0)) +
                       (location === 'beer_bar' ? numValue : (prev[itemId]?.beer_bar || 0)) +
                       (location === 'lobby' ? numValue : (prev[itemId]?.lobby || 0)) +
                       (location === 'storage_room' ? numValue : (prev[itemId]?.storage_room || 0))
        }
      }));
    } catch (error) {
      console.error('Error updating count:', error);
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

  // Update order quantity
  const updateOrderQty = (itemId, value) => {
    const newQtys = { ...orderQtys, [itemId]: parseInt(value) || 0 };
    setOrderQtys(newQtys);
    localStorage.setItem('orderQtys', JSON.stringify(newQtys));
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

  // Get suggested order quantity
  const getSuggestedOrder = (item) => {
    const have = getTotalStock(item.id);
    const target = item.target_stock || item.max_stock || 0;
    const need = Math.max(0, target - have);
    if (item.units_per_case > 1) {
      return Math.ceil(need / item.units_per_case);
    }
    return need;
  };

  // Generate orders by supplier
  const generateOrders = () => {
    const orders = {};
    
    items.forEach(item => {
      const qty = orderQtys[item.id] !== undefined ? orderQtys[item.id] : getSuggestedOrder(item);
      if (qty > 0) {
        const supplier = item.primary_supplier || 'Other';
        if (!orders[supplier]) orders[supplier] = [];
        orders[supplier].push({
          ...item,
          orderQty: qty,
          orderUnits: item.units_per_case > 1 ? qty * item.units_per_case : qty,
          cost: item.units_per_case > 1 
            ? qty * (parseFloat(item.cost_per_case) || parseFloat(item.cost_per_unit) * item.units_per_case)
            : qty * parseFloat(item.cost_per_unit)
        });
      }
    });
    
    return orders;
  };

  // Copy order list
  const copyOrderList = (supplier, orderItems) => {
    let text = `Order for ${supplier}:\n\n`;
    let total = 0;
    
    orderItems.forEach(item => {
      const unit = item.units_per_case > 1 ? 'cases' : 'units';
      text += `• ${item.name}: ${item.orderQty} ${unit}\n`;
      total += item.cost;
    });
    
    text += `\nTotal: ฿${total.toFixed(0)}`;
    
    setCopyText(text);
    setCopyDialogOpen(true);
  };

  // Save item
  const saveItem = async (itemData) => {
    try {
      if (editingItem?.id) {
        await axios.put(`${API}/items/${editingItem.id}`, itemData);
      } else {
        await axios.post(`${API}/items`, itemData);
      }
      setEditDialogOpen(false);
      loadData();
      toast({ title: "Item saved!" });
    } catch (error) {
      console.error('Error saving item:', error);
      toast({ title: "Error saving item", variant: "destructive" });
    }
  };

  // Duplicate item
  const duplicateItem = (item) => {
    setEditingItem({
      ...item,
      id: null,
      name: `${item.name} (copy)`
    });
    setEditDialogOpen(true);
  };

  // Delete item
  const deleteItem = async (itemId) => {
    if (!window.confirm('Delete this item?')) return;
    try {
      await axios.delete(`${API}/items/${itemId}`);
      loadData();
      toast({ title: "Item deleted" });
    } catch (error) {
      toast({ title: "Error deleting item", variant: "destructive" });
    }
  };

  // Group items by category and sub-category
  const groupItems = (itemsList) => {
    const groups = {};
    itemsList.forEach(item => {
      const cat = item.category_name || 'Other';
      const sub = item.sub_category || '';
      const key = sub ? `${cat} - ${sub}` : cat;
      if (!groups[key]) groups[key] = { category: cat, subCategory: sub, items: [] };
      groups[key].items.push(item);
    });
    
    // Sort groups and items within groups
    const sortedKeys = Object.keys(groups).sort();
    sortedKeys.forEach(key => {
      groups[key].items.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0) || a.name.localeCompare(b.name));
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 pb-20">
      <div className="container mx-auto px-2 sm:px-4 py-4">
        {/* Header */}
        <div className="mb-4 text-center">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Bar Stock Manager</h1>
          <p className="text-gray-600 text-xs sm:text-sm">{items.length} items tracked</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-4">
            <TabsTrigger value="count" className="text-xs sm:text-sm">Count</TabsTrigger>
            <TabsTrigger value="inventory" className="text-xs sm:text-sm">Inventory</TabsTrigger>
            <TabsTrigger value="orders" className="text-xs sm:text-sm">Orders</TabsTrigger>
            <TabsTrigger value="manage" className="text-xs sm:text-sm">Manage</TabsTrigger>
            <TabsTrigger value="accounting" className="text-xs sm:text-sm">Accounting</TabsTrigger>
          </TabsList>

          {/* COUNT TAB */}
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
                  const count = stockCounts[item.id] || {};
                  const showCase = item.bought_by_case && item.units_per_case > 1;
                  
                  return (
                    <Card key={item.id} className="shadow-sm">
                      <div className="px-2 py-1.5 border-b flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{item.name}</span>
                          {item.units_per_case > 1 && (
                            <Badge variant="outline" className="text-xs">{item.units_per_case}/case</Badge>
                          )}
                        </div>
                        <div className="text-lg font-bold text-blue-600">
                          {getTotalStock(item.id)}
                        </div>
                      </div>
                      <div className="p-1.5 grid grid-cols-2 sm:grid-cols-4 gap-1">
                        {[
                          { key: 'main_bar', label: 'Bar', bg: 'bg-orange-200' },
                          { key: 'beer_bar', label: 'Beer', bg: 'bg-yellow-200' },
                          { key: 'lobby', label: 'Lobby', bg: 'bg-blue-200' },
                          { key: 'storage_room', label: 'Storage', bg: 'bg-green-200' }
                        ].map(loc => (
                          <div key={loc.key} className={`${loc.bg} rounded px-2 py-1 flex items-center`}>
                            <span className="text-xs font-medium w-12">{loc.label}</span>
                            <Input
                              type="number"
                              inputMode="numeric"
                              min="0"
                              value={count[loc.key] || ''}
                              onChange={(e) => updateCount(item.id, loc.key, e.target.value)}
                              className="w-14 h-6 text-center font-bold text-sm bg-white ml-auto"
                              placeholder="0"
                            />
                          </div>
                        ))}
                      </div>
                    </Card>
                  );
                })}
              </div>
            ))}
          </TabsContent>

          {/* INVENTORY TAB */}
          <TabsContent value="inventory" className="space-y-3">
            <Card className="bg-green-50 border-green-200">
              <CardContent className="p-3">
                <h3 className="font-semibold text-green-900 text-sm">Full Inventory Overview</h3>
                <p className="text-xs text-green-700">Review stock levels and set order quantities</p>
              </CardContent>
            </Card>

            {/* Inventory Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-xs sm:text-sm">
                <thead className="bg-gray-100 sticky top-0">
                  <tr>
                    <th className="text-left p-2">Item</th>
                    <th className="text-center p-2">Have</th>
                    <th className="text-center p-2">Cases</th>
                    <th className="text-center p-2">Target</th>
                    <th className="text-center p-2">Need</th>
                    <th className="text-center p-2 bg-blue-100">Order</th>
                    <th className="text-left p-2">Vendor</th>
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
                        const target = item.target_stock || item.max_stock || 0;
                        const need = Math.max(0, target - have);
                        const cases = getCases(have, item.units_per_case);
                        const suggested = getSuggestedOrder(item);
                        const orderQty = orderQtys[item.id] !== undefined ? orderQtys[item.id] : suggested;
                        const isCase = item.units_per_case > 1;
                        
                        return (
                          <tr key={item.id} className="border-b hover:bg-gray-50">
                            <td className="p-2 font-medium">{item.name}</td>
                            <td className={`p-2 text-center ${have < target * 0.25 ? 'text-red-600 font-bold' : ''}`}>{have}</td>
                            <td className="p-2 text-center text-gray-500">{cases || '-'}</td>
                            <td className="p-2 text-center">{target}</td>
                            <td className="p-2 text-center">{need > 0 ? need : '-'}</td>
                            <td className="p-2 text-center bg-blue-50">
                              <Input
                                type="number"
                                min="0"
                                value={orderQty}
                                onChange={(e) => updateOrderQty(item.id, e.target.value)}
                                className="w-14 h-6 text-center font-bold text-sm mx-auto"
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
              Generate Orders →
            </Button>
          </TabsContent>

          {/* ORDERS TAB */}
          <TabsContent value="orders" className="space-y-3">
            {Object.keys(orders).length === 0 ? (
              <Card className="text-center py-8">
                <CardContent>
                  <p className="text-gray-500">No orders to place. Adjust quantities in Inventory tab.</p>
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
                            <Copy className="w-3 h-3 mr-1" />
                            Copy
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
                              {item.units_per_case > 1 && (
                                <span className="text-xs text-gray-500 ml-2">({item.orderUnits} units)</span>
                              )}
                            </div>
                            <div className="text-right">
                              <span className="font-bold">{item.orderQty} {item.units_per_case > 1 ? 'cases' : 'units'}</span>
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

            <Button 
              onClick={() => {
                localStorage.removeItem('orderQtys');
                setOrderQtys({});
                toast({ title: "Order quantities cleared" });
              }}
              variant="outline"
              className="w-full"
            >
              Clear All Orders
            </Button>
          </TabsContent>

          {/* MANAGE TAB */}
          <TabsContent value="manage" className="space-y-3">
            <Card>
              <CardHeader className="py-3 flex flex-row items-center justify-between">
                <CardTitle className="text-base">Manage Items</CardTitle>
                <Button size="sm" onClick={() => { setEditingItem(null); setEditDialogOpen(true); }}>
                  <Plus className="w-4 h-4 mr-1" /> Add Item
                </Button>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y max-h-[60vh] overflow-y-auto">
                  {items.sort((a, b) => a.name.localeCompare(b.name)).map(item => (
                    <div key={item.id} className="px-3 py-2 flex items-center justify-between hover:bg-gray-50">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm truncate">{item.name}</div>
                        <div className="text-xs text-gray-500">
                          {item.category_name} {item.sub_category && `• ${item.sub_category}`} • {item.primary_supplier} • ฿{parseFloat(item.cost_per_unit).toFixed(0)}/unit
                        </div>
                      </div>
                      <div className="flex gap-1 shrink-0">
                        <Button variant="ghost" size="sm" onClick={() => { setEditingItem(item); setEditDialogOpen(true); }}>
                          Edit
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => duplicateItem(item)}>
                          Dup
                        </Button>
                        <Button variant="ghost" size="sm" className="text-red-600" onClick={() => deleteItem(item.id)}>
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ACCOUNTING TAB */}
          <TabsContent value="accounting" className="space-y-3">
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-base">Usage & Cost Analysis</CardTitle>
                <p className="text-xs text-gray-500">Compare sessions to track usage and spending</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label className="text-xs">Opening Count (From)</Label>
                      <Select>
                        <SelectTrigger className="h-8 text-sm">
                          <SelectValue placeholder="Select session" />
                        </SelectTrigger>
                        <SelectContent>
                          {sessions.map(s => (
                            <SelectItem key={s.id} value={s.id}>
                              {s.session_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-xs">Closing Count (To)</Label>
                      <Select>
                        <SelectTrigger className="h-8 text-sm">
                          <SelectValue placeholder="Select session" />
                        </SelectTrigger>
                        <SelectContent>
                          {sessions.map(s => (
                            <SelectItem key={s.id} value={s.id}>
                              {s.session_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <Button className="w-full" disabled>
                    Generate Usage Report
                  </Button>

                  <p className="text-center text-gray-500 text-sm py-4">
                    Usage reports coming soon.<br/>
                    Will show: Opening stock + Purchases - Closing stock = Usage × Cost
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Saved Sessions */}
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-base">Saved Sessions</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y max-h-60 overflow-y-auto">
                  {sessions.length === 0 ? (
                    <p className="text-center text-gray-500 py-4 text-sm">No saved sessions yet</p>
                  ) : (
                    sessions.map(session => (
                      <div key={session.id} className="px-3 py-2">
                        <div className="font-medium text-sm">{session.session_name}</div>
                        <div className="text-xs text-gray-500">
                          {new Date(session.session_date).toLocaleString()}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Edit Item Dialog */}
        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingItem?.id ? 'Edit Item' : 'Add Item'}</DialogTitle>
            </DialogHeader>
            <ItemForm
              item={editingItem}
              onSave={saveItem}
              onCancel={() => setEditDialogOpen(false)}
            />
          </DialogContent>
        </Dialog>

        {/* Copy Dialog */}
        <Dialog open={copyDialogOpen} onOpenChange={setCopyDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Copy Order List</DialogTitle>
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

        <Toaster />
      </div>
    </div>
  );
}

// Item Form Component
function ItemForm({ item, onSave, onCancel }) {
  const [form, setForm] = useState({
    name: item?.name || '',
    category: item?.category || 'B',
    category_name: item?.category_name || 'Beer',
    sub_category: item?.sub_category || '',
    units_per_case: item?.units_per_case || 1,
    target_stock: item?.target_stock || item?.max_stock || 0,
    sort_order: item?.sort_order || 0,
    primary_supplier: item?.primary_supplier || 'Makro',
    cost_per_unit: item?.cost_per_unit || 0,
    cost_per_case: item?.cost_per_case || 0,
    bought_by_case: item?.bought_by_case || false
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(form);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <Label className="text-xs">Name</Label>
        <Input
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label className="text-xs">Category</Label>
          <Select
            value={form.category_name}
            onValueChange={(val) => {
              const cat = defaultCategories.find(c => c.label === val);
              setForm({ ...form, category: cat?.value || 'O', category_name: val });
            }}
          >
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {defaultCategories.map(c => (
                <SelectItem key={c.label} value={c.label}>{c.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label className="text-xs">Sub-Category (optional)</Label>
          <Input
            value={form.sub_category}
            onChange={(e) => setForm({ ...form, sub_category: e.target.value })}
            placeholder="e.g. Tequila, Vodka"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label className="text-xs">Units per Case</Label>
          <Input
            type="number"
            min="1"
            value={form.units_per_case}
            onChange={(e) => setForm({ ...form, units_per_case: parseInt(e.target.value) || 1 })}
          />
        </div>
        <div>
          <Label className="text-xs">Target Stock</Label>
          <Input
            type="number"
            min="0"
            value={form.target_stock}
            onChange={(e) => setForm({ ...form, target_stock: parseInt(e.target.value) || 0 })}
          />
        </div>
      </div>

      <div>
        <Label className="text-xs">Supplier</Label>
        <Select
          value={form.primary_supplier}
          onValueChange={(val) => setForm({ ...form, primary_supplier: val })}
        >
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            {defaultSuppliers.map(s => (
              <SelectItem key={s} value={s}>{s}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label className="text-xs">Cost per Unit (฿)</Label>
          <Input
            type="number"
            step="0.01"
            min="0"
            value={form.cost_per_unit}
            onChange={(e) => {
              const val = parseFloat(e.target.value) || 0;
              setForm({
                ...form,
                cost_per_unit: val,
                cost_per_case: form.units_per_case > 1 ? val * form.units_per_case : val
              });
            }}
          />
        </div>
        <div>
          <Label className="text-xs">Cost per Case (฿)</Label>
          <Input
            type="number"
            step="0.01"
            min="0"
            value={form.cost_per_case}
            onChange={(e) => setForm({ ...form, cost_per_case: parseFloat(e.target.value) || 0 })}
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="bought_by_case"
          checked={form.bought_by_case}
          onChange={(e) => setForm({ ...form, bought_by_case: e.target.checked })}
          className="rounded"
        />
        <Label htmlFor="bought_by_case" className="text-xs">Usually bought by case</Label>
      </div>

      <div className="flex gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} className="flex-1">Cancel</Button>
        <Button type="submit" className="flex-1">
          <CheckCircle className="w-4 h-4 mr-1" /> Save
        </Button>
      </div>
    </form>
  );
}

function App() {
  return <StockManager />;
}

export default App;
