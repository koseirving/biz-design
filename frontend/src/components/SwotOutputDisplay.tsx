'use client';

import React, { useState } from 'react';

interface SwotQuadrant {
  title: string;
  description: string;
  items: string[];
  color: string;
}

interface SwotData {
  type: string;
  company_name?: string;
  quadrants: {
    strengths: SwotQuadrant;
    weaknesses: SwotQuadrant;
    opportunities: SwotQuadrant;
    threats: SwotQuadrant;
  };
  matrix_layout: {
    top_left: string;
    top_right: string;
    bottom_left: string;
    bottom_right: string;
  };
}

interface SwotOutputDisplayProps {
  swotData: SwotData;
  title?: string;
  showExportOptions?: boolean;
  className?: string;
}

export default function SwotOutputDisplay({ 
  swotData, 
  title, 
  showExportOptions = true,
  className = '' 
}: SwotOutputDisplayProps) {
  const [exportFormat, setExportFormat] = useState<'png' | 'pdf' | 'json'>('png');

  const getQuadrantColorClasses = (color: string) => {
    const colorMap = {
      green: 'bg-green-50 border-green-200
      red: 'bg-red-50 border-red-200
      blue: 'bg-blue-50 border-blue-200
      orange: 'bg-orange-50 border-orange-200
    };
    return colorMap[color as keyof typeof colorMap] || 'bg-gray-50 border-gray-200
  };

  const getTextColorClasses = (color: string) => {
    const colorMap = {
      green: 'text-green-800
      red: 'text-red-800 
      blue: 'text-blue-800
      orange: 'text-orange-800
    };
    return colorMap[color as keyof typeof colorMap] || 'text-gray-800
  };

  const handleExport = async () => {
    // Export functionality would be implemented here
    console.log(`Exporting SWOT analysis as ${exportFormat}`);
    // This would integrate with libraries like jsPDF, html2canvas, etc.
  };

  const renderQuadrant = (quadrantKey: string, quadrant: SwotQuadrant) => (
    <div
      key={quadrantKey}
      className={`p-6 rounded-lg border-2 ${getQuadrantColorClasses(quadrant.color)} transition-all hover:shadow-md`}
    >
      <div className="mb-4">
        <h3 className={`text-lg font-bold ${getTextColorClasses(quadrant.color)}`}>
          {quadrant.title}
        </h3>
        <p className={`text-sm ${getTextColorClasses(quadrant.color)} opacity-75`}>
          {quadrant.description}
        </p>
      </div>
      
      <div className="space-y-2">
        {quadrant.items && quadrant.items.length > 0 ? (
          quadrant.items.map((item, index) => (
            <div
              key={index}
              className={`p-3 rounded ${getQuadrantColorClasses(quadrant.color).replace('50', '100').replace('900', '800')} ${getTextColorClasses(quadrant.color)}`}
            >
              <p className="text-sm leading-relaxed">{item}</p>
            </div>
          ))
        ) : (
          <div className={`p-3 rounded border-2 border-dashed ${quadrant.color === 'green' ? 'border-green-300' : quadrant.color === 'red' ? 'border-red-300' : quadrant.color === 'blue' ? 'border-blue-300' : 'border-orange-300'} text-center`}>
            <p className="text-sm text-gray-500">データがありません</p>
          </div>
        )}
      </div>
      
      <div className="mt-4 text-right">
        <span className={`text-xs ${getTextColorClasses(quadrant.color)} opacity-75`}>
          {quadrant.items?.length || 0} 項目
        </span>
      </div>
    </div>
  );

  return (
    <div className={`bg-white shadow-lg rounded-lg overflow-hidden ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-gray-800">
              {title || 'SWOT分析結果'}
            </h2>
            {swotData.company_name && (
              <p className="text-sm text-gray-600">
                対象: {swotData.company_name}
              </p>
            )}
          </div>
          
          {showExportOptions && (
            <div className="flex items-center space-x-2">
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as any)}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="png">PNG画像</option>
                <option value="pdf">PDF</option>
                <option value="json">JSONデータ</option>
              </select>
              <button
                onClick={handleExport}
                className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                エクスポート
              </button>
            </div>
          )}
        </div>
      </div>

      {/* SWOT Matrix */}
      <div className="p-6">
        {/* Axis Labels */}
        <div className="mb-4 text-center">
          <div className="inline-flex items-center space-x-8 text-sm font-medium text-gray-600">
            <div className="flex flex-col items-center">
              <span className="mb-2">内部環境</span>
              <div className="w-px h-4 bg-gray-300"></div>
            </div>
            <div className="text-center">
              <span>SWOT分析マトリクス</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="mb-2">外部環境</span>
              <div className="w-px h-4 bg-gray-300"></div>
            </div>
          </div>
        </div>

        {/* 2x2 Grid */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          {/* Top Row */}
          <div className="space-y-2">
            <div className="text-center text-sm font-medium text-gray-600 mb-2">
              プラス要因
            </div>
            {renderQuadrant(swotData.matrix_layout.top_left, swotData.quadrants[swotData.matrix_layout.top_left as keyof typeof swotData.quadrants])}
          </div>
          
          <div className="space-y-2">
            <div className="text-center text-sm font-medium text-gray-600 mb-2">
              プラス要因
            </div>
            {renderQuadrant(swotData.matrix_layout.top_right, swotData.quadrants[swotData.matrix_layout.top_right as keyof typeof swotData.quadrants])}
          </div>

          {/* Bottom Row */}
          <div className="space-y-2">
            <div className="text-center text-sm font-medium text-gray-600 mb-2">
              マイナス要因
            </div>
            {renderQuadrant(swotData.matrix_layout.bottom_left, swotData.quadrants[swotData.matrix_layout.bottom_left as keyof typeof swotData.quadrants])}
          </div>
          
          <div className="space-y-2">
            <div className="text-center text-sm font-medium text-gray-600 mb-2">
              マイナス要因
            </div>
            {renderQuadrant(swotData.matrix_layout.bottom_right, swotData.quadrants[swotData.matrix_layout.bottom_right as keyof typeof swotData.quadrants])}
          </div>
        </div>

        {/* Summary Statistics */}
        <div className="border-t border-gray-200 pt-4">
          <div className="grid grid-cols-4 gap-4 text-center">
            {Object.entries(swotData.quadrants).map(([key, quadrant]) => (
              <div key={key} className="p-3 bg-gray-50 rounded">
                <div className={`text-lg font-bold ${getTextColorClasses(quadrant.color)}`}>
                  {quadrant.items?.length || 0}
                </div>
                <div className="text-xs text-gray-500 capitalize">
                  {key}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Strategic Insights */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold text-gray-800 mb-2">
            戦略的示唆
          </h4>
          <div className="space-y-2 text-sm text-gray-600">
            <p>• SO戦略: 強みを活かして機会を最大化</p>
            <p>• ST戦略: 強みを使って脅威に対抗</p>
            <p>• WO戦略: 弱みを改善して機会を活用</p>
            <p>• WT戦略: 弱みと脅威の影響を最小化</p>
          </div>
        </div>
      </div>
    </div>
  );
}