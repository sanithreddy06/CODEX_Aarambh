export interface Product {
  id: number;
  title: string;
  price: number;
  stock: number;
  category: string;
}

export const fetchProducts = async (): Promise<Product[]> => {
  const res = await fetch('/api/v1/products');
  return res.json();
};

export const placeOrder = async (orderData: { userId: number; items: any[]; address: string }) => {
  const res = await fetch('/api/v1/orders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData)
  });
  return res.json();
};
