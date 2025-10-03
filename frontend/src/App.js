import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Label } from './components/ui/label';
import { Textarea } from './components/ui/textarea';
import { Separator } from './components/ui/separator';
import { useToast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';
import { Copy, Package, Calculator, Edit, Plus, Trash2, Save, X, CheckCircle, AlertCircle } from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const categoryColors = {
  'B': 'bg-amber-100 text-amber-800 border-amber-200',
  'A': 'bg-red-100 text-red-800 border-red-200',
  'M': 'bg-blue-100 text-blue-800 border-blue-200',
  'O': 'bg-green-100 text-green-800 border-green-200',
  'Z': 'bg-purple-100 text-purple-800 border-purple-200'
};

const supplierColors = {
  'Singha99': 'bg-emerald-600',
  'Makro': 'bg-orange-500',
  'Local Market': 'bg-indigo-500',
  'zBKK': 'bg-purple-600',
  'Tesco': 'bg-blue-500',
  'Other': 'bg-gray-500'
};

const categories = [
  { value: 'B', label: 'Beer' },
  { value: 'A', label: 'Thai Alcohol' },
  { value: 'A', label: 'Import Alcohol' },
  { value: 'M', label: 'Mixers' },
  { value: 'O', label: 'Other Bar' },
  { value: 'Z', label: 'Hostel Supplies' }
];

const suppliers = [
  'Singha99', 'Makro', 'Local Market', 'zBKK', 'Tesco', 'Big C', 'Vendor', 'Samui Shops', 'Mr DIY', 'Haad Rin', 'Jacky Chang', 'Other'
];

function CopyTextDialog({ text, supplier, open, onOpenChange }) {
  const copyToClipboard = () => {
    navigator.clipboard.writeText(text).then(() => {
      onOpenChange(false);
    }).catch(() => {
      // Fallback - select the text area for manual copying
      const textArea = document.getElementById('copy-text-area');
      if (textArea) {
        textArea.select();
        textArea.focus();
      }
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Copy Order for {supplier}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <Textarea
            id="copy-text-area"
            value={text}
            readOnly
            className="min-h-[300px] font-mono text-sm"
            data-testid="copy-text-area"
          />
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Close
            </Button>
            <Button onClick={copyToClipboard} data-testid="copy-button">
              <Copy className="w-4 h-4 mr-2" />
              Copy to Clipboard
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function ItemEditDialog({ item, isNew, onSave, onCancel, open, onOpenChange }) {
  const [formData, setFormData] = useState({
    name: '',
    category: 'B',
    category_name: 'Beer',
    units_per_case: 1,
    min_stock: 0,
    max_stock: 0,
    primary_supplier: 'Singha99',
    cost_per_unit: 0,
    cost_per_case: 0
  });

  useEffect(() => {
    if (item && !isNew) {
      setFormData(item);
    } else if (isNew) {
      setFormData({
        name: '',
        category: 'B',
        category_name: 'Beer',
        units_per_case: 1,
        min_stock: 0,
        max_stock: 0,
        primary_supplier: 'Singha99',
        cost_per_unit: 0,
        cost_per_case: 0
      });
    }
  }, [item, isNew]);

  const handleSave = () => {
    // Auto-calculate cost per case if not provided
    if (formData.cost_per_case === 0 && formData.cost_per_unit > 0 && formData.units_per_case > 1) {
      formData.cost_per_case = formData.cost_per_unit * formData.units_per_case;
    }
    onSave(formData);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isNew ? 'Add New Item' : 'Edit Item'}</DialogTitle>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Item Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="e.g. Big Chang, Vodka"
              />
            </div>
            <div>
              <Label htmlFor="category">Category</Label>
              <Select value={formData.category_name} onValueChange={(value) => {
                const cat = value === 'Beer' ? 'B' : 
                           value === 'Thai Alcohol' || value === 'Import Alcohol' ? 'A' :
                           value === 'Mixers' ? 'M' :
                           value === 'Other Bar' ? 'O' : 'Z';
                setFormData({...formData, category: cat, category_name: value});
              }}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Beer">Beer</SelectItem>
                  <SelectItem value="Thai Alcohol">Thai Alcohol</SelectItem>
                  <SelectItem value="Import Alcohol">Import Alcohol</SelectItem>
                  <SelectItem value="Mixers">Mixers</SelectItem>
                  <SelectItem value="Other Bar">Other Bar</SelectItem>
                  <SelectItem value="Hostel Supplies">Hostel Supplies</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="units_per_case">Units per Case/Box</Label>
              <Input
                id="units_per_case"
                type="number"
                min="1"
                value={formData.units_per_case}
                onChange={(e) => setFormData({...formData, units_per_case: parseInt(e.target.value) || 1})}
              />
            </div>
            <div>
              <Label htmlFor="min_stock">Min Stock</Label>
              <Input
                id="min_stock"
                type="number"
                min="0"
                value={formData.min_stock}
                onChange={(e) => setFormData({...formData, min_stock: parseInt(e.target.value) || 0})}
              />
            </div>
            <div>
              <Label htmlFor="max_stock">Max Stock</Label>
              <Input
                id="max_stock"
                type="number"
                min="0"
                value={formData.max_stock}
                onChange={(e) => setFormData({...formData, max_stock: parseInt(e.target.value) || 0})}
              />
            </div>
          </div>

          <div>
            <Label htmlFor="supplier">Primary Supplier</Label>
            <Select value={formData.primary_supplier} onValueChange={(value) => setFormData({...formData, primary_supplier: value})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {suppliers.map(supplier => (
                  <SelectItem key={supplier} value={supplier}>{supplier}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="cost_per_unit">Cost per Unit (฿)</Label>
              <Input
                id="cost_per_unit"
                type="number"
                step="0.01"
                min="0"
                value={formData.cost_per_unit}
                onChange={(e) => setFormData({...formData, cost_per_unit: parseFloat(e.target.value) || 0})}
              />
            </div>
            <div>
              <Label htmlFor="cost_per_case">Cost per Case (฿)</Label>
              <Input
                id="cost_per_case"
                type="number"
                step="0.01"
                min="0"
                value={formData.cost_per_case}
                onChange={(e) => setFormData({...formData, cost_per_case: parseFloat(e.target.value) || 0})}
                placeholder={formData.units_per_case > 1 && formData.cost_per_unit > 0 ? 
                  `Auto: ${(formData.cost_per_unit * formData.units_per_case).toFixed(2)}` : ''}
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel}>
            <X className="w-4 h-4 mr-2" />
            Cancel
          </Button>
          <Button onClick={handleSave}>
            <Save className="w-4 h-4 mr-2" />
            {isNew ? 'Add Item' : 'Save Changes'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function StockCounter() {
  const [items, setItems] = useState([]);
  const [stockCounts, setStockCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('count');
  const [shoppingList, setShoppingList] = useState({});
  const [quickRestock, setQuickRestock] = useState([]);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [isNewItem, setIsNewItem] = useState(false);
  const [copyDialogOpen, setCopyDialogOpen] = useState(false);
  const [copyText, setCopyText] = useState('');
  const [copySupplier, setCopySupplier] = useState('');
  const [currentSession, setCurrentSession] = useState(null);
  const { toast } = useToast();

  useEffect(() => {
    loadItems();
    loadStockCounts();
    loadCurrentSession();
  }, []);

  const loadItems = async () => {
    try {
      const response = await axios.get(`${API}/items`);
      if (response.data.length === 0) {
        // Initialize with real data if no items exist
        await initializeRealData();
      } else {
        setItems(response.data);
      }
    } catch (error) {
      console.error('Error loading items:', error);
      await initializeRealData();
    }
  };

  const initializeRealData = async () => {
    try {
      await axios.post(`${API}/initialize-real-data`);
      const response = await axios.get(`${API}/items`);
      setItems(response.data);
      toast({
        title: "Real inventory data loaded",
        description: "Your bar inventory system is ready to use",
      });
    } catch (error) {
      console.error('Error initializing real data:', error);
    }
  };

  const loadStockCounts = async () => {
    try {
      const response = await axios.get(`${API}/stock-counts`);
      const countsMap = {};
      response.data.forEach(count => {
        countsMap[count.item_id] = count;
      });
      setStockCounts(countsMap);
      setLoading(false);
    } catch (error) {
      console.error('Error loading stock counts:', error);
      setLoading(false);
    }
  };

  const loadCurrentSession = async () => {
    try {
      const response = await axios.get(`${API}/stock-sessions/current`);
      if (response.data) {
        setCurrentSession(response.data);
      }
    } catch (error) {
      console.error('Error loading current session:', error);
    }
  };

  const saveStockCountSession = async () => {
    const sessionName = prompt("Enter session name (e.g., 'Pre-Party Stock Count - October 3'):"); 
    if (!sessionName) return;

    try {
      const sessionData = {
        session_name: sessionName,
        session_type: "full_count",
        notes: `Stock count completed with ${Object.keys(stockCounts).length} items counted`
      };
      
      const response = await axios.post(`${API}/stock-sessions`, sessionData);
      setCurrentSession(response.data);
      
      toast({
        title: "Stock count saved!",
        description: `Session "${sessionName}" has been saved to history`,
      });
    } catch (error) {
      console.error('Error saving stock session:', error);
      toast({
        title: "Error saving session",
        description: "Could not save stock count session",
        variant: "destructive",
      });
    }
  };

  const updateStockCount = async (itemId, location, value) => {
    try {
      const updateData = {};
      updateData[location] = parseInt(value) || 0;
      
      await axios.put(`${API}/stock-counts/${itemId}`, updateData);
      
      // Reload stock counts to get fresh data
      loadStockCounts();

      // Auto-save indication (no toast spam)
    } catch (error) {
      console.error('Error updating stock count:', error);
      toast({
        title: "Error",
        description: "Failed to update stock count",
        variant: "destructive",
      });
    }
  };

  const loadShoppingList = async () => {
    try {
      const response = await axios.get(`${API}/shopping-list`);
      setShoppingList(response.data);
    } catch (error) {
      console.error('Error loading shopping list:', error);
    }
  };

  const loadQuickRestock = async () => {
    try {
      const response = await axios.get(`${API}/quick-restock`);
      setQuickRestock(response.data);
    } catch (error) {
      console.error('Error loading quick restock:', error);
    }
  };

  const showCopyDialog = async (supplier) => {
    try {
      const response = await axios.get(`${API}/shopping-list-text/${supplier}`);
      setCopyText(response.data.text);
      setCopySupplier(supplier);
      setCopyDialogOpen(true);
    } catch (error) {
      console.error('Error loading copy text:', error);
      toast({
        title: "Error",
        description: "Could not prepare copy text",
        variant: "destructive",
      });
    }
  };

  const handleEditItem = (item) => {
    setEditingItem(item);
    setIsNewItem(false);
    setEditDialogOpen(true);
  };

  const handleAddItem = () => {
    setEditingItem(null);
    setIsNewItem(true);
    setEditDialogOpen(true);
  };

  const handleSaveItem = async (itemData) => {
    try {
      if (isNewItem) {
        await axios.post(`${API}/items`, itemData);
        toast({
          title: "Item added",
          description: "New item added successfully",
        });
      } else {
        await axios.put(`${API}/items/${editingItem.id}`, itemData);
        toast({
          title: "Item updated",
          description: "Item updated successfully",
        });
      }
      
      setEditDialogOpen(false);
      loadItems(); // Reload items
    } catch (error) {
      console.error('Error saving item:', error);
      toast({
        title: "Error",
        description: "Failed to save item",
        variant: "destructive",
      });
    }
  };

  const handleDeleteItem = async (item) => {
    if (confirm(`Are you sure you want to delete "${item.name}"?`)) {
      try {
        await axios.delete(`${API}/items/${item.id}`);
        toast({
          title: "Item deleted",
          description: "Item deleted successfully",
        });
        loadItems();
      } catch (error) {
        console.error('Error deleting item:', error);
        toast({
          title: "Error",
          description: "Failed to delete item",
          variant: "destructive",
        });
      }
    }
  };

  useEffect(() => {
    if (activeTab === 'shopping') {
      loadShoppingList();
    } else if (activeTab === 'quick') {
      loadQuickRestock();
    }
  }, [activeTab]);

  const getTotalCostBySupplier = (items) => {
    return items.reduce((total, item) => total + item.estimated_cost, 0);
  };

  const getTotalItemsCounted = () => {
    return Object.values(stockCounts).reduce((total, count) => total + count.total_count, 0);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading inventory system...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 pb-16">
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2" data-testid="app-title">
            Bar Stock Manager
          </h1>
          <p className="text-gray-600 text-sm">Track inventory across all locations • Case calculations included</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-6" data-testid="main-tabs">
            <TabsTrigger value="count" data-testid="count-tab" className="text-sm">Count</TabsTrigger>
            <TabsTrigger value="shopping" data-testid="shopping-tab" className="text-sm">Shopping</TabsTrigger>
            <TabsTrigger value="quick" data-testid="quick-tab" className="text-sm">Alerts</TabsTrigger>
            <TabsTrigger value="manage" data-testid="manage-tab" className="text-sm">Manage</TabsTrigger>
          </TabsList>

          <TabsContent value="count" className="space-y-4" data-testid="count-content">
            {/* Stock Count Session Header */}
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-5 w-5 text-blue-600" />
                    <div>
                      <h3 className="font-semibold text-blue-900">Stock Count Session</h3>
                      <p className="text-sm text-blue-700">
                        {currentSession ? 
                          `Active: ${currentSession.session_name}` : 
                          'No active session - counts will be saved automatically'
                        }
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-blue-700 border-blue-300">
                      {getTotalItemsCounted()} items counted
                    </Badge>
                    <Button 
                      onClick={saveStockCountSession}
                      size="sm"
                      data-testid="save-stock-session"
                    >
                      <Save className="w-4 h-4 mr-2" />
                      Save Session
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-3">
              {items.map(item => {
                const count = stockCounts[item.id] || { main_bar: 0, beer_bar: 0, lobby: 0, storage_room: 0, total_count: 0 };
                
                return (
                  <Card key={item.id} className="border-l-4 border-l-blue-500 shadow-sm hover:shadow-md transition-all duration-200" data-testid={`item-card-${item.id}`}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-sm font-semibold">{item.name}</CardTitle>
                          <Badge className={`${categoryColors[item.category]} text-xs`}>
                            {item.category_name}
                          </Badge>
                          {item.units_per_case > 1 && (
                            <Badge variant="outline" className="text-xs">
                              <Package className="w-3 h-3 mr-1" />
                              {item.units_per_case}/case
                            </Badge>
                          )}
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-blue-600" data-testid={`total-count-${item.id}`}>
                            {count.total_count}
                          </div>
                          <div className="text-xs text-gray-500">Total</div>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                        {[
                          { key: 'main_bar', label: 'Main Bar', icon: '🍺' },
                          { key: 'beer_bar', label: 'Beer Bar', icon: '🍻' },
                          { key: 'lobby', label: 'Lobby', icon: '🏨' },
                          { key: 'storage_room', label: 'Storage', icon: '📦' }
                        ].map(location => (
                          <div key={location.key} className="space-y-1">
                            <label className="text-xs font-medium text-gray-700 flex items-center gap-1">
                              <span>{location.icon}</span>
                              {location.label}
                            </label>
                            <Input
                              type="number"
                              min="0"
                              value={count[location.key] || ''}
                              onChange={(e) => updateStockCount(item.id, location.key, e.target.value)}
                              className="text-center font-medium h-7 text-sm"
                              placeholder="0"
                              data-testid={`count-input-${item.id}-${location.key}`}
                            />
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </TabsContent>

          <TabsContent value="shopping" className="space-y-3" data-testid="shopping-content">
            <div className="grid gap-3">
              {Object.entries(shoppingList).map(([supplier, items]) => {
                const totalCost = getTotalCostBySupplier(items);
                const supplierColor = supplierColors[supplier] || supplierColors['Other'];
                
                return (
                  <Card key={supplier} className="shadow-sm" data-testid={`supplier-card-${supplier}`}>
                    <CardHeader className={`${supplierColor} text-white rounded-t-lg py-3`}>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base font-bold">{supplier}</CardTitle>
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="bg-white/20 text-white border-white/30 text-xs">
                            ฿{totalCost.toFixed(2)}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => showCopyDialog(supplier)}
                            className="text-white hover:bg-white/20 h-7 w-7 p-0"
                            data-testid={`copy-${supplier}`}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="divide-y">
                        {items.map((item, index) => (
                          <div key={index} className="p-2 hover:bg-gray-50 transition-colors" data-testid={`shopping-item-${item.item_id}`}>
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <h4 className="font-medium text-gray-900 text-xs">{item.item_name}</h4>
                                <div className="text-xs text-gray-500 mt-1 flex items-center gap-3">
                                  <span>Now: {item.current_stock}</span>
                                  <span>Max: {item.max_stock}</span>
                                  {item.case_calculation.cases_to_buy > 0 && (
                                    <span className="flex items-center gap-1 text-blue-600">
                                      <Calculator className="w-3 h-3" />
                                      {item.case_calculation.display_text}
                                    </span>
                                  )}
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="text-xs font-bold text-green-600">
                                  {item.case_calculation.cases_to_buy > 0 
                                    ? `${item.case_calculation.cases_to_buy} cases` 
                                    : `${item.need_to_buy_units} units`}
                                </div>
                                <div className="text-xs text-gray-600">
                                  ฿{item.estimated_cost.toFixed(2)}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
              
              {Object.keys(shoppingList).length === 0 && (
                <Card className="text-center py-8" data-testid="no-shopping-items">
                  <CardContent>
                    <div className="text-4xl mb-4">✅</div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">All Stocked Up!</h3>
                    <p className="text-gray-600 text-sm">No items need restocking at the moment.</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="quick" className="space-y-4" data-testid="quick-content">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <AlertCircle className="h-4 w-4 text-red-500" />
                  Low Stock Alert
                </CardTitle>
                <p className="text-gray-600 text-sm">Items below minimum stock levels</p>
              </CardHeader>
              <CardContent>
                {quickRestock.length === 0 ? (
                  <div className="text-center py-6">
                    <div className="text-3xl mb-3">✅</div>
                    <p className="text-gray-600 text-sm">All items are above minimum stock levels</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {quickRestock.map((item, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-red-50 border border-red-200 rounded-lg" data-testid={`low-stock-${item.item_id}`}>
                        <div>
                          <h4 className="font-medium text-gray-900 text-sm">{item.item_name}</h4>
                          <p className="text-xs text-gray-600">{item.category} • {item.primary_supplier}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-bold text-red-600">
                            {item.current_stock} / {item.min_stock} min
                          </div>
                          <div className="text-xs text-red-500">
                            Need {item.min_stock - item.current_stock} more
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="manage" className="space-y-4" data-testid="manage-content">
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">Manage Items</CardTitle>
                    <p className="text-gray-600 text-sm">Add, edit, or remove items from your inventory</p>
                  </div>
                  <Button onClick={handleAddItem} data-testid="add-item-btn" size="sm">
                    <Plus className="w-4 h-4 mr-1" />
                    Add Item
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {items.map(item => (
                    <div key={item.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50" data-testid={`manage-item-${item.id}`}>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-sm">{item.name}</h4>
                          <Badge className={`${categoryColors[item.category]} text-xs`}>
                            {item.category_name}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {item.primary_supplier}
                          </Badge>
                          {item.units_per_case > 1 && (
                            <Badge variant="outline" className="text-xs">
                              {item.units_per_case}/case
                            </Badge>
                          )}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          Min: {item.min_stock} • Max: {item.max_stock} • Unit: ฿{item.cost_per_unit}
                          {item.cost_per_case > 0 && ` • Case: ฿${item.cost_per_case}`}
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEditItem(item)}
                          data-testid={`edit-item-${item.id}`}
                          className="h-7 w-7 p-0"
                        >
                          <Edit className="w-3 h-3" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteItem(item)}
                          className="text-red-600 hover:text-red-700 h-7 w-7 p-0"
                          data-testid={`delete-item-${item.id}`}
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <ItemEditDialog
          item={editingItem}
          isNew={isNewItem}
          onSave={handleSaveItem}
          onCancel={() => setEditDialogOpen(false)}
          open={editDialogOpen}
          onOpenChange={setEditDialogOpen}
        />

        <CopyTextDialog
          text={copyText}
          supplier={copySupplier}
          open={copyDialogOpen}
          onOpenChange={setCopyDialogOpen}
        />

        <Toaster />
      </div>
      
      {/* Bottom spacing for last input accessibility */}
      <div className="h-20"></div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<StockCounter />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;