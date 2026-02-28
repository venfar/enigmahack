import type { Data } from "./types";

export const HEADERS: Record<keyof Data, string> = {
  date: 'Дата',
  fio: 'ФИО',
  object_name: 'Объект',
  phone: 'Телефон',
  email: 'Email',
  serial_numbers: 'Заводские номера',
  device_type: 'Тип приборов',
  sentiment: 'Эмоциональный окрас',
  answer: 'Суть вопроса',
};