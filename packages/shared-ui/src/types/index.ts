export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface ApiError {
  detail: string;
  status: number;
}

export interface SelectOption {
  value: string;
  label: string;
}
