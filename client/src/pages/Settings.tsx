import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsApi } from '../services/api';
import Card from '../components/Card';
import Button from '../components/Button';
import Input, { Textarea } from '../components/Input';

export default function Settings() {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState(false);

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.getAll,
  });

  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  const saveMutation = useMutation({
    mutationFn: settingsApi.updateBulk,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    saveMutation.mutate(formData);
  };

  const updateField = (key: string, value: string) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

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
      <div className="mb-6 lg:mb-10">
        <h1 className="font-serif text-2xl lg:text-4xl font-semibold text-champagne-800 mb-1 lg:mb-2">
          הגדרות
        </h1>
        <p className="text-champagne-700 text-sm lg:text-base">ניהול הגדרות הסטודיו</p>
        <div className="gold-accent mt-3 lg:mt-4 w-12 lg:w-16"></div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Studio Info */}
        <Card className="p-4 lg:p-6" hover={false}>
          <h2 className="font-serif text-lg lg:text-xl font-semibold text-champagne-800 mb-4">
            פרטי הסטודיו
          </h2>
          <div className="space-y-4">
            <Input
              label="שם הסטודיו"
              value={formData.studio_name || ''}
              onChange={(e) => updateField('studio_name', e.target.value)}
              placeholder="Rachel"
            />
            <Input
              label="תת-כותרת"
              value={formData.studio_subtitle || ''}
              onChange={(e) => updateField('studio_subtitle', e.target.value)}
              placeholder="השכרת שמלות יוקרה"
            />
          </div>
        </Card>

        {/* WhatsApp Templates */}
        <Card className="p-4 lg:p-6" hover={false}>
          <h2 className="font-serif text-lg lg:text-xl font-semibold text-champagne-800 mb-4">
            תבניות הודעות WhatsApp
          </h2>
          <p className="text-sm text-champagne-600 mb-4">
            השתמש ב: {'{customer_name}'}, {'{dress_name}'}, {'{date}'}, {'{time}'}
          </p>
          <div className="space-y-4">
            <Textarea
              label="תזכורת החזרה"
              value={formData.whatsapp_return_template || ''}
              onChange={(e) => updateField('whatsapp_return_template', e.target.value)}
              rows={4}
            />
            <Textarea
              label="תזכורת מדידה"
              value={formData.whatsapp_fitting_template || ''}
              onChange={(e) => updateField('whatsapp_fitting_template', e.target.value)}
              rows={4}
            />
            <Textarea
              label="תזכורת איסוף"
              value={formData.whatsapp_pickup_template || ''}
              onChange={(e) => updateField('whatsapp_pickup_template', e.target.value)}
              rows={4}
            />
            <Textarea
              label="הודעת תודה"
              value={formData.whatsapp_thankyou_template || ''}
              onChange={(e) => updateField('whatsapp_thankyou_template', e.target.value)}
              rows={4}
            />
          </div>
        </Card>

        {/* Save Button */}
        <div className="flex items-center gap-4">
          <Button type="submit" disabled={saveMutation.isPending}>
            {saveMutation.isPending ? 'שומר...' : 'שמור הגדרות'}
          </Button>
          {saved && (
            <span className="text-emerald-600 text-sm font-medium">
              ✓ ההגדרות נשמרו בהצלחה
            </span>
          )}
        </div>
      </form>
    </div>
  );
}
