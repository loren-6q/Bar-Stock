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
  'Makro': 'bg-orange-500',
  'Singha99': 'bg-emerald-500',
  'Local Market': 'bg-indigo-500',
  'Tesco': 'bg-blue-500',
  'Other': 'bg-gray-500'
};

function StockCounter() {
  const [items, setItems] = useState([]);
  const [stockCounts, setStockCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('count');
  const [shoppingList, setShoppingList] = useState({});
  const { toast } = useToast();

  useEffect(() => {
    loadItems();
    loadStockCounts();
  }, []);

  const loadItems = async () => {
    try {
      const response = await axios.get(`${API}/items`);
      setItems(response.data);
    } catch (error) {
      console.error('Error loading items:', error);
      if (error.response?.status === 404 || !items.length) {
        // Try to initialize sample data
        await initializeSampleData();
      }
    }
  };

  const initializeSampleData = async () => {
    try {
      await axios.post(`${API}/initialize-sample-data`);
      toast({
        title: "Sample data loaded",
        description: "Sample bar inventory has been initialized",
      });
      loadItems();
    } catch (error) {
      console.error('Error initializing sample data:', error);
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
      
      // Update local state
      setStockCounts(prev => {
        const current = prev[itemId] || { item_id: itemId, main_bar: 0, beer_bar: 0, lobby: 0, storage_room: 0, total_count: 0 };
        const updated = { ...current, [location]: parseInt(value) || 0 };
        updated.total_count = updated.main_bar + updated.beer_bar + updated.lobby + updated.storage_room;
        return { ...prev, [itemId]: updated };
      });

      toast({
        title: "Count updated",
        description: "Stock count has been saved",
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

  useEffect(() => {
    if (activeTab === 'shopping') {
      loadShoppingList();
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
          <p className="text-gray-600">Track inventory across all locations</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8" data-testid="main-tabs">
            <TabsTrigger value="count" data-testid="count-tab">Stock Count</TabsTrigger>
            <TabsTrigger value="shopping" data-testid="shopping-tab">Shopping List</TabsTrigger>
            <TabsTrigger value="quick" data-testid="quick-tab">Quick Check</TabsTrigger>
          </TabsList>

          <TabsContent value="count" className="space-y-6" data-testid="count-content">
            <div className="grid gap-6">
              {items.map(item => {
                const count = stockCounts[item.id] || { main_bar: 0, beer_bar: 0, lobby: 0, storage_room: 0, total_count: 0 };
                
                return (
                  <Card key={item.id} className="border-l-4 border-l-blue-500 shadow-sm hover:shadow-md transition-all duration-200" data-testid={`item-card-${item.id}`}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <CardTitle className="text-lg font-semibold">{item.name}</CardTitle>
                          <Badge className={`${categoryColors[item.category]} text-xs`}>
                            {item.category_name}
                          </Badge>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-blue-600" data-testid={`total-count-${item.id}`}>
                            {count.total_count}
                          </div>
                          <div className="text-sm text-gray-500">Total Count</div>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[
                          { key: 'main_bar', label: 'Main Bar', icon: '🍺' },
                          { key: 'beer_bar', label: 'Beer Bar', icon: '🍻' },
                          { key: 'lobby', label: 'Lobby', icon: '🏨' },
                          { key: 'storage_room', label: 'Storage', icon: '📦' }
                        ].map(location => (
                          <div key={location.key} className="space-y-2">
                            <label className="text-sm font-medium text-gray-700 flex items-center gap-1">
                              <span>{location.icon}</span>
                              {location.label}
                            </label>
                            <Input
                              type="number"
                              min="0"
                              value={count[location.key] || ''}
                              onChange={(e) => updateStockCount(item.id, location.key, e.target.value)}
                              className="text-center font-medium"
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

          <TabsContent value="shopping" className="space-y-6" data-testid="shopping-content">
            <div className="grid gap-6">
              {Object.entries(shoppingList).map(([supplier, items]) => {
                const totalCost = getTotalCostBySupplier(items);
                const supplierColor = supplierColors[supplier] || supplierColors['Other'];
                
                return (
                  <Card key={supplier} className="shadow-lg" data-testid={`supplier-card-${supplier}`}>
                    <CardHeader className={`${supplierColor} text-white rounded-t-lg`}>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-xl font-bold">{supplier}</CardTitle>
                        <Badge variant="secondary" className="bg-white/20 text-white border-white/30">
                          ฿{totalCost.toFixed(2)}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="divide-y">
                        {items.map((item, index) => (
                          <div key={index} className="p-4 hover:bg-gray-50 transition-colors" data-testid={`shopping-item-${item.item_id}`}>
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <h4 className="font-semibold text-gray-900">{item.item_name}</h4>
                                <div className="text-sm text-gray-500 mt-1">
                                  Current: {item.current_stock} | Need: {item.need_to_buy} | Target: {item.max_stock}
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="text-lg font-bold text-green-600">
                                  {item.need_to_buy} units
                                </div>
                                <div className="text-sm text-gray-600">
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

          <TabsContent value="quick" className="space-y-6" data-testid="quick-content">
            <Card>
              <CardHeader>
                <CardTitle>Quick Nightly Restock Check</CardTitle>
                <p className="text-gray-600">Items running low that need attention</p>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <div className="text-4xl mb-4">🔄</div>
                  <p className="text-gray-600">Feature coming soon - Quick restock alerts</p>
                </div>
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