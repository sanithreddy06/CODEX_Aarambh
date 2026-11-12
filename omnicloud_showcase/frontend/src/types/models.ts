export interface UserProfile {
  id: number;
  username: string;
  email: string;
  role: 'customer' | 'admin';
}

export interface OrderRecord {
  id: number;
  total_amount: number;
  status: 'pending' | 'processing' | 'shipped' | 'cancelled';
  items_count: number;
}
