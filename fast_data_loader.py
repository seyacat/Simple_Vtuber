#!/usr/bin/env python3
"""
Optimized data loader for fast TensorFlow training.
"""

import numpy as np
import json
import tensorflow as tf

class FastDataLoader:
    """Fast data loader with caching and prefetching"""
    
    def __init__(self, data_dir='dataset/numpy'):
        self.data_dir = data_dir
        self.features = None
        self.labels = None
        self.label_names = None
        self.num_classes = None
        
    def load(self):
        """Load data with caching"""
        if self.features is None:
            # Load from compressed format
            data = np.load(f'{self.data_dir}/dataset_compressed.npz')
            self.features = data['features']
            self.labels = data['labels']
            self.label_names = data['label_names']
            
            # Load metadata
            with open(f'{self.data_dir}/metadata.json', 'r') as f:
                metadata = json.load(f)
            
            self.num_classes = len(self.label_names)
            
            print(f"Loaded {len(self.features)} samples")
            print(f"Features shape: {self.features.shape}")
            print(f"Labels shape: {self.labels.shape}")
            print(f"Number of classes: {self.num_classes}")
        
        return self.features, self.labels, self.label_names
    
    def get_tf_dataset(self, batch_size=32, shuffle=True, prefetch=True):
        """Create TensorFlow Dataset for optimal performance"""
        features, labels, _ = self.load()
        
        # Convert to categorical
        labels_categorical = tf.keras.utils.to_categorical(labels, self.num_classes)
        
        # Create dataset
        dataset = tf.data.Dataset.from_tensor_slices((features, labels_categorical))
        
        if shuffle:
            dataset = dataset.shuffle(buffer_size=len(features))
        
        dataset = dataset.batch(batch_size)
        
        if prefetch:
            dataset = dataset.prefetch(tf.data.AUTOTUNE)
        
        return dataset
    
    def get_train_val_split(self, validation_split=0.2, batch_size=32):
        """Get train/validation split with optimal performance"""
        features, labels, _ = self.load()
        
        # Calculate split index
        split_idx = int(len(features) * (1 - validation_split))
        
        # Split features and labels
        train_features = features[:split_idx]
        train_labels = labels[:split_idx]
        val_features = features[split_idx:]
        val_labels = labels[split_idx:]
        
        # Convert to categorical
        train_labels_cat = tf.keras.utils.to_categorical(train_labels, self.num_classes)
        val_labels_cat = tf.keras.utils.to_categorical(val_labels, self.num_classes)
        
        # Create datasets
        train_dataset = tf.data.Dataset.from_tensor_slices((train_features, train_labels_cat))
        train_dataset = train_dataset.shuffle(buffer_size=len(train_features))
        train_dataset = train_dataset.batch(batch_size)
        train_dataset = train_dataset.prefetch(tf.data.AUTOTUNE)
        
        val_dataset = tf.data.Dataset.from_tensor_slices((val_features, val_labels_cat))
        val_dataset = val_dataset.batch(batch_size)
        val_dataset = val_dataset.prefetch(tf.data.AUTOTUNE)
        
        return train_dataset, val_dataset

# Example usage
if __name__ == '__main__':
    loader = FastDataLoader()
    features, labels, label_names = loader.load()
    print(f"Label names: {label_names}")
    
    # Get TensorFlow dataset
    dataset = loader.get_tf_dataset(batch_size=32)
    print(f"Dataset created with automatic prefetching")
    
    # Get train/val split
    train_ds, val_ds = loader.get_train_val_split(validation_split=0.2)
    print(f"Train samples: {len(train_ds)*32} (estimated)")
    print(f"Validation samples: {len(val_ds)*32} (estimated)")
