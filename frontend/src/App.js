import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Separator } from './components/ui/separator';
import { useToast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';
import { Copy, Package, Calculator } from 'lucide-react';
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

function StockCounter() {
  const [items, setItems] = useState([]);
  const [stockCounts, setStockCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('count');
  const [shoppingList, setShoppingList] = useState({});
  const [quickRestock, setQuickRestock] = useState([]);
  const { toast } = useToast();

  useEffect(() => {
    loadItems();
    loadStockCounts();
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

  const updateStockCount = async (itemId, location, value) => {
    try {
      const updateData = {};
      updateData[location] = parseInt(value) || 0;
      
      await axios.put(`${API}/stock-counts/${itemId}`, updateData);
      
      // Reload stock counts to get fresh data
      loadStockCounts();

      toast({
        title: "Count updated",
        description: "Stock count saved successfully",
      });
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

  const copyToClipboard = async (supplier) => {
    try {
      const response = await axios.get(`${API}/shopping-list-text/${supplier}`);
      
      // Try modern clipboard API first
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(response.data.text);
      } else {
        // Fallback for older browsers or non-HTTPS
        const textArea = document.createElement('textarea');
        textArea.value = response.data.text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        textArea.remove();
      }
      
      toast({
        title: "Copied to clipboard!",
        description: `${supplier} order list copied for messaging`,
      });
    } catch (error) {
      console.error('Error copying to clipboard:', error);
      toast({
        title: "Copy failed", 
        description: "Could not copy to clipboard. Try selecting and copying manually.",
        variant: "destructive",
      });
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2" data-testid="app-title">
            Bar Stock Manager
          </h1>
          <p className="text-gray-600">Track inventory across all locations • Case calculations included</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8" data-testid="main-tabs">
            <TabsTrigger value="count" data-testid="count-tab">Stock Count</TabsTrigger>
            <TabsTrigger value="shopping" data-testid="shopping-tab">Shopping List</TabsTrigger>
            <TabsTrigger value="quick" data-testid="quick-tab">Low Stock Alert</TabsTrigger>
          </TabsList>

          <TabsContent value="count" className="space-y-4" data-testid="count-content">
            <div className="grid gap-4">
              {items.map(item => {
                const count = stockCounts[item.id] || { main_bar: 0, beer_bar: 0, lobby: 0, storage_room: 0, total_count: 0 };
                
                return (
                  <Card key={item.id} className="border-l-4 border-l-blue-500 shadow-sm hover:shadow-md transition-all duration-200" data-testid={`item-card-${item.id}`}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <CardTitle className="text-base font-semibold">{item.name}</CardTitle>
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
                          <div className="text-xl font-bold text-blue-600" data-testid={`total-count-${item.id}`}>
                            {count.total_count}
                          </div>
                          <div className="text-xs text-gray-500">Total</div>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
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
                              className="text-center font-medium h-8 text-sm"
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

          <TabsContent value="shopping" className="space-y-4" data-testid="shopping-content">
            <div className="grid gap-4">
              {Object.entries(shoppingList).map(([supplier, items]) => {
                const totalCost = getTotalCostBySupplier(items);
                const supplierColor = supplierColors[supplier] || supplierColors['Other'];
                
                return (
                  <Card key={supplier} className="shadow-lg" data-testid={`supplier-card-${supplier}`}>
                    <CardHeader className={`${supplierColor} text-white rounded-t-lg`}>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg font-bold">{supplier}</CardTitle>
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="bg-white/20 text-white border-white/30">
                            ฿{totalCost.toFixed(2)}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyToClipboard(supplier)}
                            className="text-white hover:bg-white/20 h-8 w-8 p-0"
                            data-testid={`copy-${supplier}`}
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="divide-y">
                        {items.map((item, index) => (
                          <div key={index} className="p-3 hover:bg-gray-50 transition-colors" data-testid={`shopping-item-${item.item_id}`}>
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <h4 className="font-medium text-gray-900 text-sm">{item.item_name}</h4>
                                <div className="text-xs text-gray-500 mt-1 flex items-center gap-4">
                                  <span>Current: {item.current_stock}</span>
                                  <span>Target: {item.max_stock}</span>
                                  {item.case_calculation.cases_to_buy > 0 && (
                                    <span className="flex items-center gap-1 text-blue-600">
                                      <Calculator className="w-3 h-3" />
                                      {item.case_calculation.display_text}
                                    </span>
                                  )}
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="text-sm font-bold text-green-600">
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
                <Card className="text-center py-12" data-testid="no-shopping-items">
                  <CardContent>
                    <div className="text-6xl mb-4">✅</div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">All Stocked Up!</h3>
                    <p className="text-gray-600">No items need restocking at the moment.</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="quick" className="space-y-4" data-testid="quick-content">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span className="text-red-500">⚠️</span>
                  Low Stock Alert
                </CardTitle>
                <p className="text-gray-600">Items below minimum stock levels</p>
              </CardHeader>
              <CardContent>
                {quickRestock.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">✅</div>
                    <p className="text-gray-600">All items are above minimum stock levels</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {quickRestock.map((item, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg" data-testid={`low-stock-${item.item_id}`}>
                        <div>
                          <h4 className="font-medium text-gray-900">{item.item_name}</h4>
                          <p className="text-sm text-gray-600">{item.category} • {item.primary_supplier}</p>
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
        </Tabs>

        <Toaster />
      </div>
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