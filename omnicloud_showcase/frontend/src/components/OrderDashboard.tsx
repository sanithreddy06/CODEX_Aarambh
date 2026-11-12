import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/apiClient';
import { OrderRecord } from '../types/models';

export const OrderDashboard: React.FC = () => {
  const [orders, setOrders] = useState<OrderRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.fetchOrders().then((data) => {
      setOrders(data);
      setLoading(false);
    });
  }, []);

  const handleCreateSample = async () => {
    await apiClient.createOrder({
      customer_id: 42,
      shipping_address: '100 Innovation Way',
      items: [{ product_id: 1, quantity: 2, unit_price: 29.99 }]
    });
  };

  return (
    <div className="p-6 bg-slate-900 text-white rounded-xl">
      <h2 className="text-xl font-bold">Enterprise Order Management</h2>
      <button onClick={handleCreateSample} className="mt-4 px-4 py-2 bg-indigo-600 rounded">
        Submit Order
      </button>
      {loading ? <p>Loading orders...</p> : <p>Total Orders Loaded: {orders.length}</p>}
    </div>
  );
};
