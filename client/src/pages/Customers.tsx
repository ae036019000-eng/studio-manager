import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { customersApi } from '../services/api';
import Card from '../components/Card';
import Button from '../components/Button';
import Modal from '../components/Modal';
import Input, { Textarea } from '../components/Input';
import Table from '../components/Table';
import SearchFilter from '../components/SearchFilter';
import type { Customer, Rental } from '../types';

export default function Customers() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    address: '',
    notes: '',
  });

  const { data: customers = [], isLoading } = useQuery({
    queryKey: ['customers'],
    queryFn: customersApi.getAll,
  });

  const { data: customerRentals = [] } = useQuery({
    queryKey: ['customer-rentals', selectedCustomer?.id],
    queryFn: () => selectedCustomer ? customersApi.getRentals(selectedCustomer.id) : Promise.resolve([]),
    enabled: !!selectedCustomer,
  });

  const createMutation = useMutation({
    mutationFn: customersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      closeModal();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => customersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      closeModal();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: customersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
    onError: (error: Error) => {
      alert(error.message);
    },
  });

  const openModal = (customer?: Customer) => {
    if (customer) {
      setEditingCustomer(customer);
      setFormData({
        name: customer.name,
        phone: customer.phone || '',
        email: customer.email || '',
        address: customer.address || '',
        notes: customer.notes || '',
      });
    } else {
      setEditingCustomer(null);
      setFormData({
        name: '',
        phone: '',
        email: '',
        address: '',
        notes: '',
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingCustomer(null);
  };

  const openHistoryModal = (customer: Customer) => {
    setSelectedCustomer(customer);
    setIsHistoryModalOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (editingCustomer) {
      updateMutation.mutate({ id: editingCustomer.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const filteredCustomers = customers.filter((customer: Customer) =>
    customer.name.toLowerCase().includes(search.toLowerCase()) ||
    customer.phone?.includes(search) ||
    customer.email?.toLowerCase().includes(search.toLowerCase())
  );

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('he-IL');
  };

  const columns = [
    { key: 'name', header: 'שם' },
    { key: 'phone', header: 'טלפון' },
    { key: 'email', header: 'אימייל' },
    {
      key: 'created_at',
      header: 'תאריך הצטרפות',
      render: (c: Customer) => formatDate(c.created_at),
    },
    {
      key: 'actions',
      header: '',
      render: (c: Customer) => (
        <div className="flex gap-2 justify-end">
          <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); openHistoryModal(c); }}>
            היסטוריה
          </Button>
          <Button size="sm" variant="secondary" onClick={(e) => { e.stopPropagation(); openModal(c); }}>
            עריכה
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={(e) => {
              e.stopPropagation();
              if (confirm('האם למחוק את הלקוח?')) {
                deleteMutation.mutate(c.id);
              }
            }}
          >
            ✕
          </Button>
        </div>
      ),
    },
  ];

  const historyColumns = [
    { key: 'dress_name', header: 'שמלה' },
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
      key: 'status',
      header: 'סטטוס',
      render: (r: Rental) => {
        const styles: Record<string, string> = {
          active: 'bg-sky-50 text-sky-700',
          completed: 'bg-emerald-50 text-emerald-700',
          cancelled: 'bg-rose-50 text-rose-700',
        };
        const labels: Record<string, string> = {
          active: 'פעיל',
          completed: 'הושלם',
          cancelled: 'בוטל',
        };
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[r.status]}`}>
            {labels[r.status] || r.status}
          </span>
        );
      },
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
    <div className="animate-slide-up pb-20 lg:pb-0">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6 lg:mb-10">
        <div>
          <h1 className="font-serif text-2xl lg:text-4xl font-semibold text-champagne-800 mb-1 lg:mb-2">
            לקוחות
          </h1>
          <p className="text-champagne-700 text-sm lg:text-base">ניהול רשימת הלקוחות</p>
          <div className="gold-accent mt-3 lg:mt-4 w-12 lg:w-16"></div>
        </div>
        <Button onClick={() => openModal()} className="w-full sm:w-auto">
          + הוסף לקוח
        </Button>
      </div>

      {/* Search */}
      <div className="mb-6 lg:mb-8">
        <SearchFilter
          value={search}
          onChange={setSearch}
          placeholder="חיפוש לפי שם, טלפון או אימייל..."
        />
      </div>

      {/* Mobile Cards */}
      <div className="lg:hidden space-y-3">
        {filteredCustomers.length === 0 ? (
          <Card className="p-8 text-center">
            <div className="text-champagne-300 text-4xl mb-4">✦</div>
            <p className="text-champagne-700">אין לקוחות להצגה</p>
          </Card>
        ) : (
          filteredCustomers.map((customer: Customer) => (
            <Card key={customer.id} className="p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-serif text-lg font-semibold text-champagne-800">{customer.name}</h3>
                  {customer.phone && (
                    <a href={`tel:${customer.phone}`} className="text-sm text-gold-600">{customer.phone}</a>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="secondary" onClick={() => openModal(customer)}>
                    עריכה
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      if (confirm('האם למחוק את הלקוח?')) {
                        deleteMutation.mutate(customer.id);
                      }
                    }}
                  >
                    ✕
                  </Button>
                </div>
              </div>
              {customer.email && (
                <p className="text-sm text-champagne-600 truncate">{customer.email}</p>
              )}
              <div className="flex justify-between items-center mt-3 pt-3 border-t border-champagne-100">
                <span className="text-xs text-champagne-500">הצטרף/ה: {formatDate(customer.created_at)}</span>
                <Button size="sm" variant="ghost" onClick={() => openHistoryModal(customer)}>
                  היסטוריה
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
          data={filteredCustomers}
          keyField="id"
          emptyMessage="אין לקוחות להצגה"
        />
      </Card>

      {/* Add/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingCustomer ? 'עריכת לקוח' : 'הוספת לקוח חדש'}
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          <Input
            label="שם מלא"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
            placeholder="שם פרטי ומשפחה"
          />

          <Input
            label="טלפון"
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            placeholder="050-0000000"
          />

          <Input
            label="אימייל"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="email@example.com"
          />

          <Input
            label="כתובת"
            value={formData.address}
            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            placeholder="עיר, רחוב"
          />

          <Textarea
            label="הערות"
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            rows={3}
            placeholder="הערות נוספות..."
          />

          <div className="flex justify-end gap-4 pt-6 border-t border-champagne-100">
            <Button type="button" variant="secondary" onClick={closeModal}>
              ביטול
            </Button>
            <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
              {editingCustomer ? 'עדכון' : 'הוספה'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* History Modal */}
      <Modal
        isOpen={isHistoryModalOpen}
        onClose={() => setIsHistoryModalOpen(false)}
        title={`היסטוריית השכרות - ${selectedCustomer?.name}`}
        size="lg"
      >
        <Table
          columns={historyColumns}
          data={customerRentals}
          keyField="id"
          emptyMessage="אין היסטוריית השכרות"
        />
      </Modal>
    </div>
  );
}
