import { Router } from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { v2 as cloudinary } from 'cloudinary';

const router = Router();

// Check if using Cloudinary (production) or local storage (development)
const useCloudinary = !!process.env.CLOUDINARY_CLOUD_NAME;

if (useCloudinary) {
  cloudinary.config({
    cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
    api_key: process.env.CLOUDINARY_API_KEY,
    api_secret: process.env.CLOUDINARY_API_SECRET,
  });
  console.log('Using Cloudinary for image storage');
} else {
  console.log('Using local storage for images');
}

// Ensure uploads directory exists for local storage
const uploadsDir = path.join(__dirname, '..', '..', '..', 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadsDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + path.extname(file.originalname));
  }
});

// For Cloudinary, use memory storage
const memoryStorage = multer.memoryStorage();

const upload = multer({
  storage: useCloudinary ? memoryStorage : storage,
  limits: {
    fileSize: 20 * 1024 * 1024 // 20MB limit
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png|gif|webp/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);

    if (extname && mimetype) {
      cb(null, true);
    } else {
      cb(new Error('רק קבצי תמונה מותרים (JPEG, PNG, GIF, WebP)'));
    }
  }
});

// Upload single image
router.post('/', (req, res) => {
  upload.single('image')(req, res, async (err) => {
    if (err) {
      if (err instanceof multer.MulterError) {
        if (err.code === 'LIMIT_FILE_SIZE') {
          return res.status(400).json({ error: 'הקובץ גדול מדי. מקסימום 20MB' });
        }
        return res.status(400).json({ error: `שגיאה בהעלאה: ${err.message}` });
      }
      return res.status(400).json({ error: err.message || 'שגיאה בהעלאת הקובץ' });
    }

    if (!req.file) {
      return res.status(400).json({ error: 'לא נבחר קובץ' });
    }

    try {
      if (useCloudinary) {
        // Upload to Cloudinary
        const result = await new Promise<any>((resolve, reject) => {
          const uploadStream = cloudinary.uploader.upload_stream(
            {
              folder: 'studio-manager',
              resource_type: 'image',
            },
            (error, result) => {
              if (error) reject(error);
              else resolve(result);
            }
          );
          uploadStream.end(req.file!.buffer);
        });

        res.json({ path: result.secure_url, filename: result.public_id });
      } else {
        // Local storage
        const imagePath = `/uploads/${req.file.filename}`;
        res.json({ path: imagePath, filename: req.file.filename });
      }
    } catch (error) {
      console.error('Upload error:', error);
      res.status(500).json({ error: 'שגיאה בהעלאת התמונה' });
    }
  });
});

// Delete image
router.delete('/:filename', async (req, res) => {
  try {
    if (useCloudinary) {
      // Delete from Cloudinary
      await cloudinary.uploader.destroy(req.params.filename);
    } else {
      // Delete from local storage
      const filePath = path.join(uploadsDir, req.params.filename);
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
      }
    }
    res.json({ message: 'File deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete file' });
  }
});

export default router;
