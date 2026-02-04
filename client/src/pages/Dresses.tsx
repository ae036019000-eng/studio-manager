import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dressesApi, uploadApi } from '../services/api';
import Card from '../components/Card';
import Button from '../components/Button';
import Modal from '../components/Modal';
import Input, { Textarea, Select } from '../components/Input';
import SearchFilter from '../components/SearchFilter';
import type { Dress } from '../types';

const statusOptions = [
  { value: 'available', label: 'פנויה' },
  { value: 'rented', label: 'מושכרת' },
  { value: 'maintenance', label: 'בתחזוקה' },
];

const sizeOptions = [
  { value: '', label: 'בחר מידה' },
  { value: 'XS', label: 'XS' },
  { value: 'S', label: 'S' },
  { value: 'M', label: 'M' },
  { value: 'L', label: 'L' },
  { value: 'XL', label: 'XL' },
  { value: 'XXL', label: 'XXL' },
];

export default function Dresses() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDress, setEditingDress] = useState<Dress | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    size: '',
    color: '',
    rental_price: '',
    image_path: '',
    status: 'available',
  });

  const { data: dresses = [], isLoading } = useQuery({
    queryKey: ['dresses'],
    queryFn: dressesApi.getAll,
  });

  const createMutation = useMutation({
    mutationFn: dressesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dresses'] });
      closeModal();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => dressesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dresses'] });
      closeModal();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: dressesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dresses'] });
    },
  });

  const openModal = (dress?: Dress) => {
    setUploadError(null);
    if (dress) {
      setEditingDress(dress);
      setFormData({
        name: dress.name,
        description: dress.description || '',
        size: dress.size || '',
        color: dress.color || '',
        rental_price: String(dress.rental_price),
        image_path: dress.image_path || '',
        status: dress.status,
      });
    } else {
      setEditingDress(null);
      setFormData({
        name: '',
        description: '',
        size: '',
        color: '',
        rental_price: '',
        image_path: '',
        status: 'available',
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingDress(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      ...formData,
      rental_price: parseFloat(formData.rental_price) || 0,
    };

    if (editingDress) {
      updateMutation.mutate({ id: editingDress.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setIsUploading(true);
      setUploadError(null);
      try {
        const result = await uploadApi.uploadImage(file);
        setFormData({ ...formData, image_path: result.path });
      } catch (error) {
        const message = error instanceof Error ? error.message : 'שגיאה בהעלאת התמונה';
        setUploadError(message);
      } finally {
        setIsUploading(false);
      }
    }
  };

  const filteredDresses = dresses.filter((dress: Dress) =>
    dress.name.toLowerCase().includes(search.toLowerCase()) ||
    dress.color?.toLowerCase().includes(search.toLowerCase()) ||
    dress.size?.toLowerCase().includes(search.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      available: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      rented: 'bg-sky-50 text-sky-700 border-sky-200',
      maintenance: 'bg-amber-50 text-amber-700 border-amber-200',
    };
    const labels: Record<string, string> = {
      available: 'פנויה',
      rented: 'מושכרת',
      maintenance: 'בתחזוקה',
    };
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${styles[status] || 'bg-gray-50'}`}>
        {labels[status] || status}
      </span>
    );
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('he-IL', {
      style: 'currency',
      currency: 'ILS',
    }).format(amount);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-500 text-4xl animate-pulse">◈</div>
      </div>
    );
  }

  return (
    <div className="animate-slide-up pb-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6 lg:mb-10">
        <div>
          <h1 className="font-sans text-2xl lg:text-4xl font-semibold text-gray-900 mb-1 lg:mb-2">
            שמלות
          </h1>
          <p className="text-gray-600 text-sm lg:text-base">ניהול קולקציית השמלות</p>
          <div className="gold-accent mt-3 lg:mt-4 w-12 lg:w-16"></div>
        </div>
        <Button onClick={() => openModal()} className="w-full sm:w-auto">
          + הוסף שמלה
        </Button>
      </div>

      {/* Search */}
      <div className="mb-6 lg:mb-8">
        <SearchFilter
          value={search}
          onChange={setSearch}
          placeholder="חיפוש לפי שם, צבע או מידה..."
        />
      </div>

      {/* Grid */}
      {filteredDresses.length === 0 ? (
        <Card className="p-8 lg:p-16 text-center">
          <div className="text-gray-200 text-4xl lg:text-5xl mb-4">❖</div>
          <p className="text-gray-600">אין שמלות להצגה</p>
        </Card>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 lg:gap-8">
          {filteredDresses.map((dress: Dress) => (
            <Card key={dress.id} className="overflow-hidden group">
              <div className="aspect-[3/4] bg-gradient-to-br from-gray-50 to-gray-100 relative overflow-hidden">
                {dress.image_path ? (
                  <img
                    src={dress.image_path}
                    alt={dress.name}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <span className="text-6xl text-gray-200">❖</span>
                  </div>
                )}
                <div className="absolute top-4 left-4">
                  {getStatusBadge(dress.status)}
                </div>
              </div>
              <div className="p-3 lg:p-6">
                <h3 className="font-sans text-base lg:text-xl font-semibold text-gray-900 mb-1 lg:mb-2 truncate">
                  {dress.name}
                </h3>
                <div className="text-xs lg:text-sm text-gray-600 space-x-reverse space-x-1 lg:space-x-2 rtl:space-x-reverse mb-2 lg:mb-3">
                  {dress.size && <span>מידה {dress.size}</span>}
                  {dress.size && dress.color && <span>•</span>}
                  {dress.color && <span>{dress.color}</span>}
                </div>
                <p className="text-gray-700 font-semibold text-base lg:text-lg mb-3 lg:mb-4">
                  {formatCurrency(dress.rental_price)}
                  <span className="text-gray-500 text-xs lg:text-sm font-normal"> / אירוע</span>
                </p>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => openModal(dress)}
                    className="flex-1 text-xs lg:text-sm"
                  >
                    עריכה
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      if (confirm('האם למחוק את השמלה?')) {
                        deleteMutation.mutate(dress.id);
                      }
                    }}
                  >
                    ✕
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingDress ? 'עריכת שמלה' : 'הוספת שמלה חדשה'}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          <Input
            label="שם השמלה"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
            placeholder="לדוגמה: שמלת ערב זהובה"
          />

          <Textarea
            label="תיאור"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            rows={3}
            placeholder="תיאור קצר של השמלה..."
          />

          <div className="grid grid-cols-2 gap-6">
            <Select
              label="מידה"
              value={formData.size}
              onChange={(e) => setFormData({ ...formData, size: e.target.value })}
              options={sizeOptions}
            />

            <Input
              label="צבע"
              value={formData.color}
              onChange={(e) => setFormData({ ...formData, color: e.target.value })}
              placeholder="לדוגמה: זהב"
            />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <Input
              label="מחיר השכרה (₪)"
              type="number"
              value={formData.rental_price}
              onChange={(e) => setFormData({ ...formData, rental_price: e.target.value })}
              required
              min="0"
              step="0.01"
            />

            <Select
              label="סטטוס"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              options={statusOptions}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-2 tracking-wide">
              תמונה
            </label>
            <input
              type="file"
              accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
              onChange={handleImageUpload}
              disabled={isUploading}
              className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4
                       file:rounded-xl file:border-0 file:text-sm file:font-medium
                       file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200
                       file:cursor-pointer file:transition-colors disabled:opacity-50"
            />
            {isUploading && (
              <p className="mt-2 text-sm text-gray-700">מעלה תמונה...</p>
            )}
            {uploadError && (
              <p className="mt-2 text-sm text-red-600">{uploadError}</p>
            )}
            {formData.image_path && !isUploading && (
              <div className="mt-4">
                <img
                  src={formData.image_path}
                  alt="Preview"
                  className="w-32 h-40 object-cover rounded-xl border border-gray-200"
                />
              </div>
            )}
          </div>

          <div className="flex justify-end gap-4 pt-6 border-t border-gray-100">
            <Button type="button" variant="secondary" onClick={closeModal}>
              ביטול
            </Button>
            <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
              {editingDress ? 'עדכון' : 'הוספה'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
