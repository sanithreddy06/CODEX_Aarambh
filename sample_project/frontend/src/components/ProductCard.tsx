import React from 'react';
import { Product } from '../services/apiClient';

interface Props {
  product: Product;
  onAddToCart: (product: Product) => void;
}

export const ProductCard: React.FC<Props> = ({ product, onAddToCart }) => {
  return (
    <div className="border border-neutral-800 rounded-lg p-4 bg-neutral-900 shadow-sm">
      <div className="text-xs text-neutral-400 uppercase tracking-wider">{product.category}</div>
      <h3 className="font-semibold text-lg text-white mt-1">{product.title}</h3>
      <div className="flex items-center justify-between mt-4">
        <span className="text-emerald-400 font-bold">${product.price.toFixed(2)}</span>
        <button
          onClick={() => onAddToCart(product)}
          className="px-3 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded text-sm transition"
        >
          Add to Cart
        </button>
      </div>
    </div>
  );
};
