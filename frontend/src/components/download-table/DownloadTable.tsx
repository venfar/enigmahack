import type { Data } from '../../types.ts';

type DownloadTableProps = {
  headers: Record<keyof Data, string>;
  data: Data[];
}

function DownloadTable(props: DownloadTableProps) {
  const {headers, data} = props;

  const convertToCSV = (data: Data[]) => {
    if (!data || data.length === 0) return '';

    const csvRows = [];

    csvRows.push(Object.values(headers).join(';'));

    for (const row of data) {
      const values = (Object.keys(headers) as Array<keyof Data>).map((header) => {
        const value = row[header];
        const normalized = Array.isArray(value) ? value.join(', ') : value;
        const escaped = String(normalized).replace(/"/g, '""');
        return `"${escaped}"`;
      });

      csvRows.push(values.join(';'));
    }

    return '\uFEFF' + csvRows.join('\n');
  };

  const downloadCSV = () => {
    const csvContent = convertToCSV(data);
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');

    link.setAttribute('href', url);
    link.setAttribute('download', `table-export-${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  }

  return (
    <button onClick={downloadCSV}>
      Скачать
    </button>
  )
}

export default DownloadTable;