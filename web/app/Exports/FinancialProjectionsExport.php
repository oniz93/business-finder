<?php

namespace App\Exports;

use Maatwebsite\Excel\Concerns\FromCollection;
use Maatwebsite\Excel\Concerns\WithHeadings;

class FinancialProjectionsExport implements FromCollection, WithHeadings
{
    protected $projections;

    public function __construct(array $projections)
    {
        $this->projections = $projections;
    }

    /**
    * @return \Illuminate\Support\Collection
    */
    public function collection()
    {
        // Convert the associative array to a collection of arrays for export
        $data = [];
        foreach ($this->projections as $month => $values) {
            $data[] = [
                'Month' => $month,
                'Revenue' => $values['revenue'],
                'Expenses' => $values['expenses'],
                'Profit' => $values['profit'],
                'Cumulative Profit' => $values['cumulative_profit'],
            ];
        }
        return collect($data);
    }

    public function headings(): array
    {
        return [
            'Month',
            'Revenue',
            'Expenses',
            'Profit',
            'Cumulative Profit',
        ];
    }
}
