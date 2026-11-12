import axios from 'axios';
import { OrderRecord, UserProfile } from '../types/models';

const API_BASE = '/api/v1';

export const apiClient = {
  async fetchOrders(): Promise<OrderRecord[]> {
    const res = await fetch(`${API_BASE}/orders`);
    return res.json();
  },

  async createOrder(payload: { customer_id: number; items: any[]; shipping_address: string }) {
    return axios.post(`${API_BASE}/orders`, payload);
  },

  async login(email: string, password: string) {
    return axios.post(`${API_BASE}/auth/login`, { email, password });
  }
};
