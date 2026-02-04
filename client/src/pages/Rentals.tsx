import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rentalsApi, dressesApi, customersApi, paymentsApi } from '../services/api';
import Card from '../components/Card';
import Button from '../components/Button';
import Modal from '../components/Modal';
import Input, { Textarea, Select } from '../components/Input';
import Table from '../components/Table';
import SearchFilter from '../components/SearchFilter';
import type { Rental, Dress, Customer } from '../types';

const statusOptions = [
  { value: 'active', label: 'פעיל' },
  { value: 'completed', label: 'הושלם' },
  { value: 'cancelled', label: 'בוטל' },
];

export default function Rentals() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
  const [editingRental, setEditingRental] = useState<Rental | null>(null);
  const [selectedRental, setSelectedRental] = useState<Rental | null>(null);
  const [formData, setFormData] = useState({
    dress_id: '',
    customer_id: '',
    start_date: '',
    end_date: '',
    total_price: '',
    deposit: '',
    status: 'active',
    notes: '',
  });
  const [paymentData, setPaymentData] = useState({
    amount: '',
    payment_date: new Date().toISOString().split('T')[0],
    method: 'cash',
  });

  const { data: rentals = [], isLoading } = useQuery({
    queryKey: ['rentals'],
    queryFn: rentalsApi.getAll,
  });

  const { data: dresses = [] } = useQuery({
    queryKey: ['dresses'],
    queryFn: dressesApi.getAll,
  });

  const { data: customers = [] } = useQuery({
    queryKey: ['customers'],
    queryFn: customersApi.getAll,
  });

  const createMutation = useMutation({
    mutationFn: rentalsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rentals'] });
      queryClient.invalidateQueries({ queryKey: ['dresses'] });
      closeModal();
    },
    onError: (error: Error) => {
      alert(error.message);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => rentalsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rentals'] });
      queryClient.invalidateQueries({ queryKey: ['dresses'] });
      closeModal();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: rentalsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rentals'] });
      queryClient.invalidateQueries({ queryKey: ['dresses'] });
    },
  });

  const paymentMutation = useMutation({
    mutationFn: paymentsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rentals'] });
      queryClient.invalidateQueries({ queryKey: ['payments'] });
      setIsPaymentModalOpen(false);
      setPaymentData({
        amount: '',
        payment_date: new Date().toISOString().split('T')[0],
        method: 'cash',
      });
    },
  });

  const openModal = (rental?: Rental) => {
    if (rental) {
      setEditingRental(rental);
      setFormData({
        dress_id: String(rental.dress_id),
        customer_id: String(rental.customer_id),
        start_date: rental.start_date,
        end_date: rental.end_date,
        total_price: String(rental.total_price),
        deposit: String(rental.deposit),
        status: rental.status,
        notes: rental.notes || '',
      });
    } else {
      setEditingRental(null);
      setFormData({
        dress_id: '',
        customer_id: '',
        start_date: '',
        end_date: '',
        total_price: '',
        deposit: '',
        status: 'active',
        notes: '',
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingRental(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      ...formData,
      dress_id: parseInt(formData.dress_id),
      customer_id: parseInt(formData.customer_id),
      total_price: parseFloat(formData.total_price) || 0,
      deposit: parseFloat(formData.deposit) || 0,
    };

    if (editingRental) {
      updateMutation.mutate({ id: editingRental.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handlePaymentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRental) return;

    paymentMutation.mutate({
      rental_id: selectedRental.id,
      amount: parseFloat(paymentData.amount),
      payment_date: paymentData.payment_date,
      method: paymentData.method,
    });
  };

  const fillPriceFromDress = (dressId: string) => {
    const dress = dresses.find((d: Dress) => d.id === parseInt(dressId));
    if (dress && dress.rental_price) {
      setFormData(prev => ({ ...prev, dress_id: dressId, total_price: String(dress.rental_price) }));
    } else {
      setFormData(prev => ({ ...prev, dress_id: dressId }));
    }
  };

  const filteredRentals = rentals.filter((rental: Rental) =>
    rental.dress_name?.toLowerCase().includes(search.toLowerCase()) ||
    rental.customer_name?.toLowerCase().includes(search.toLowerCase())
  );

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('he-IL');
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('he-IL', {
      style: 'currency',
      currency: 'ILS',
    }).format(amount);
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      active: 'bg-sky-50 text-sky-700 border-sky-200',
      completed: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      cancelled: 'bg-rose-50 text-rose-700 border-rose-200',
    };
    const labels: Record<string, string> = {
      active: 'פעיל',
      completed: 'הושלם',
      cancelled: 'בוטל',
    };
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${styles[status] || 'bg-gray-50'}`}>
        {labels[status] || status}
      </span>
    );
  };

  const availableDresses = editingRental
    ? dresses
    : dresses.filter((d: Dress) => d.status === 'available');

  const dressOptions = [
    { value: '', label: 'בחר שמלה' },
    ...availableDresses.map((d: Dress) => ({
      value: d.id,
      label: `${d.name} (${d.size || 'ללא מידה'})`,
    })),
  ];

  const customerOptions = [
    { value: '', label: 'בחר לקוח' },
    ...customers.map((c: Customer) => ({
      value: c.id,
      label: c.name,
    })),
  ];

  const columns = [
    { key: 'dress_name', header: 'שמלה' },
    { key: 'customer_name', header: 'לקוח/ה' },
    {
      key: 'start_date',
      header: 'מתאריך',
      render: (r: Rental) => formatDate(r.start_date),
    },
    {
      key: 'end_date',
      header: 'עד תאריך',
      render: (r: Rental) => formatDate(r.end_date),
    },
    {
      key: 'total_price',
      header: 'מחיר',
      render: (r: Rental) => (
        <span className="font-semibold text-gold-600">{formatCurrency(r.total_price)}</span>
      ),
    },
    {
      key: 'status',
      header: 'סטטוס',
      render: (r: Rental) => getStatusBadge(r.status),
    },
    {
      key: 'actions',
      header: '',
      render: (r: Rental) => (
        <div className="flex gap-2 justify-end">
          <Button
            size="sm"
            variant="primary"
            onClick={(e) => {
              e.stopPropagation();
              setSelectedRental(r);
              setIsPaymentModalOpen(true);
            }}
          >
            תשלום
          </Button>
          <Button size="sm" variant="secondary" onClick={(e) => { e.stopPropagation(); openModal(r); }}>
            עריכה
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={(e) => {
              e.stopPropagation();
              if (confirm('האם למחוק את ההשכרה?')) {
                deleteMutation.mutate(r.id);
              }
            }}
          >
            ✕
          </Button>
        </div>
      ),
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gold-400 text-4xl animate-pulse">◈</div>
      </div>
    );
  }

  return (
    <div className="animate-slide-up pb-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6 lg:mb-10">
        <div>
          <h1 className="font-serif text-2xl lg:text-4xl font-semibold text-champagne-800 mb-1 lg:mb-2">
            השכרות
          </h1>
          <p className="text-champagne-700 text-sm lg:text-base">ניהול השכרות השמלות</p>
          <div className="gold-accent mt-3 lg:mt-4 w-12 lg:w-16"></div>
        </div>
        <Button onClick={() => openModal()} className="w-full sm:w-auto">
          + השכרה חדשה
        </Button>
      </div>

      {/* Search */}
      <div className="mb-6 lg:mb-8">
        <SearchFilter
          value={search}
          onChange={setSearch}
          placeholder="חיפוש לפי שמלה או לקוח..."
        />
      </div>

      {/* Mobile Cards */}
      <div className="lg:hidden space-y-3">
        {filteredRentals.length === 0 ? (
          <Card className="p-8 text-center">
            <div className="text-champagne-300 text-4xl mb-4">◆</div>
            <p className="text-champagne-700">אין השכרות להצגה</p>
          </Card>
        ) : (
          filteredRentals.map((rental: Rental) => (
            <Card key={rental.id} className="p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className="font-serif text-base font-semibold text-champagne-800">{rental.dress_name}</h3>
                  <p className="text-sm text-champagne-600">{rental.customer_name}</p>
                </div>
                {getStatusBadge(rental.status)}
              </div>
              <div className="flex justify-between items-center text-sm text-champagne-600 mb-3">
                <span>{formatDate(rental.start_date)} - {formatDate(rental.end_date)}</span>
                <span className="font-semibold text-gold-600">{formatCurrency(rental.total_price)}</span>
              </div>
              <div className="flex gap-2 pt-3 border-t border-champagne-100">
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => {
                    setSelectedRental(rental);
                    setIsPaymentModalOpen(true);
                  }}
                  className="flex-1"
                >
                  תשלום
                </Button>
                <Button size="sm" variant="secondary" onClick={() => openModal(rental)}>
                  עריכה
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    if (confirm('האם למחוק את ההשכרה?')) {
                      deleteMutation.mutate(rental.id);
                    }
                  }}
                >
                  ✕
                </Button>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Desktop Table */}
      <Card className="overflow-hidden hidden lg:block" hover={false}>
        <Table
          columns={columns}
          data={filteredRentals}
          keyField="id"
          emptyMessage="אין השכרות להצגה"
        />
      </Card>

      {/* Add/Edit Rental Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingRental ? 'עריכת השכרה' : 'השכרה חדשה'}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
            <Select
              label="שמלה"
              value={formData.dress_id}
              onChange={(e) => fillPriceFromDress(e.target.value)}
              options={dressOptions}
              required
              disabled={!!editingRental}
            />

            <Select
              label="לקוח/ה"
              value={formData.customer_id}
              onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
              options={customerOptions}
              required
              disabled={!!editingRental}
            />
          </div>

          <div className="grid grid-cols-2 gap-4 lg:gap-6">
            <Input
              label="תאריך אירוע"
              type="date"
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
              required
            />

            <Input
              label="תאריך החזרה"
              type="date"
              value={formData.end_date}
              onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
            <Input
              label="מחיר כולל (₪)"
              type="number"
              value={formData.total_price}
              onChange={(e) => setFormData({ ...formData, total_price: e.target.value })}
              required
              min="0"
            />

            <Input
              label="פיקדון (₪)"
              type="number"
              value={formData.deposit}
              onChange={(e) => setFormData({ ...formData, deposit: e.target.value })}
              min="0"
            />

            <Select
              label="סטטוס"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              options={statusOptions}
            />
          </div>

          <Textarea
            label="הערות"
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            rows={2}
            placeholder="הערות נוספות..."
          />

          <div className="flex justify-end gap-4 pt-6 border-t border-champagne-100">
            <Button type="button" variant="secondary" onClick={closeModal}>
              ביטול
            </Button>
            <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
              {editingRental ? 'עדכון' : 'צור השכרה'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Payment Modal */}
      <Modal
        isOpen={isPaymentModalOpen}
        onClose={() => setIsPaymentModalOpen(false)}
        title="רישום תשלום"
      >
        <form onSubmit={handlePaymentSubmit} className="space-y-6">
          <div className="bg-gradient-to-br from-gold-50 to-champagne-50 p-6 rounded-xl border border-champagne-200">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-champagne-700">שמלה:</span>
                <p className="font-medium text-champagne-800">{selectedRental?.dress_name}</p>
              </div>
              <div>
                <span className="text-champagne-700">לקוח/ה:</span>
                <p className="font-medium text-champagne-800">{selectedRental?.customer_name}</p>
              </div>
              <div className="col-span-2">
                <span className="text-champagne-700">סה״כ לתשלום:</span>
                <p className="font-serif text-2xl font-bold text-gold-600 mt-1">
                  {selectedRental && formatCurrency(selectedRental.total_price)}
                </p>
              </div>
            </div>
          </div>

          <Input
            label="סכום התשלום (₪)"
            type="number"
            value={paymentData.amount}
            onChange={(e) => setPaymentData({ ...paymentData, amount: e.target.value })}
            required
            min="0"
          />

          <Input
            label="תאריך תשלום"
            type="date"
            value={paymentData.payment_date}
            onChange={(e) => setPaymentData({ ...paymentData, payment_date: e.target.value })}
            required
          />

          <Select
            label="אמצעי תשלום"
            value={paymentData.method}
            onChange={(e) => setPaymentData({ ...paymentData, method: e.target.value })}
            options={[
              { value: 'cash', label: 'מזומן' },
              { value: 'credit', label: 'אשראי' },
              { value: 'transfer', label: 'העברה בנקאית' },
              { value: 'bit', label: 'ביט' },
            ]}
          />

          <div className="flex justify-end gap-4 pt-6 border-t border-champagne-100">
            <Button type="button" variant="secondary" onClick={() => setIsPaymentModalOpen(false)}>
              ביטול
            </Button>
            <Button type="submit" disabled={paymentMutation.isPending}>
              רשום תשלום
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
