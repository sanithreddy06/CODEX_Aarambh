import React, { useEffect, useState } from 'react';
import { fetchProducts, Product } from '../services/apiClient';
import { ProductCard } from '../components/ProductCard';

export const CatalogPage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<Product[]>([]);

  useEffect(() => {
    fetchProducts().then(setProducts).catch(console.error);
  }, []);

  const handleAddToCart = (item: Product) => {
    setCart((prev) => [...prev, item]);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-white">Product Catalog</h1>
        <div className="text-neutral-400">Cart: {cart.length} items</div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {products.map((p) => (
          <ProductCard key={p.id} product={p} onAddToCart={handleAddToCart} />
        ))}
      </div>
    </div>
  );
};
