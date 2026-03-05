#!/usr/bin/env python3
"""
Convert features.json to optimized numpy format for faster loading.
"""

import json
import numpy as np
import os
import time

def convert_features():
    """Convert features.json to numpy format"""
    
    print("Converting features to optimized numpy format...")
    
    # Load features.json
    with open('dataset/features.json', 'r') as f:
        data = json.load(f)
    
    features = np.array(data['features'], dtype=np.float32)
    labels = np.array(data['labels'], dtype=np.int32)
    label_names = data['labelNames']
    
    print(f"Original features shape: {features.shape}")
    print(f"Labels shape: {labels.shape}")
    print(f"Label names: {label_names}")
    
    # Create optimized directory
    os.makedirs('dataset/numpy', exist_ok=True)
    
    # Save in numpy format for fast loading
    np.save('dataset/numpy/features.npy', features)
    np.save('dataset/numpy/labels.npy', labels)
    
    # Save metadata
    metadata = {
        'label_names': label_names,
        'num_samples': len(features),
        'feature_shape': features[0].shape,
        'conversion_date': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open('dataset/numpy/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Also save in compressed format
    np.savez_compressed(
        'dataset/numpy/dataset_compressed.npz',
        features=features,
        labels=labels,
        label_names=label_names
    )
    
    print("\nConversion complete!")
    print("Files created:")
    print("  - dataset/numpy/features.npy")
    print("  - dataset/numpy/labels.npy")
    print("  - dataset/numpy/metadata.json")
    print("  - dataset/numpy/dataset_compressed.npz")
    
    # Test loading speed
    print("\nTesting loading speed...")
    
    # Test JSON loading
    start = time.time()
    with open('dataset/features.json', 'r') as f:
        json.load(f)
    json_time = time.time() - start
    
    # Test numpy loading
    start = time.time()
    np.load('dataset/numpy/features.npy')
    numpy_time = time.time() - start
    
    # Test compressed loading
    start = time.time()
    np.load('dataset/numpy/dataset_compressed.npz')
    compressed_time = time.time() - start
    
    print(f"JSON loading time: {json_time:.4f}s")
    print(f"NumPy loading time: {numpy_time:.4f}s")
    print(f"Compressed loading time: {compressed_time:.4f}s")
    print(f"Speedup (NumPy vs JSON): {json_time/numpy_time:.1f}x faster")

def create_optimized_loader():
    """Create an optimized data loader script"""
    
    loader_code = '''#!/usr/bin/env python3
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
'''
    
    with open('fast_data_loader.py', 'w') as f:
        f.write(loader_code)
    
    print("\nCreated fast_data_loader.py")
    print("This loader provides:")
    print("  - Cached data loading")
    print("  - TensorFlow Dataset with prefetching")
    print("  - Automatic train/validation split")
    print("  - Optimal performance for GPU training")

if __name__ == '__main__':
    convert_features()
    create_optimized_loader()