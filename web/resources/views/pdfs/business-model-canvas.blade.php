<!DOCTYPE html>
<html>
<head>
    <title>Business Model Canvas - {{ $businessPlanId }}</title>
    <style>
        body {
            font-family: sans-serif;
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        .container {
            width: 100%;
            padding: 20px;
        }
        .grid-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            border: 1px solid #ccc;
            padding: 10px;
        }
        .grid-item {
            border: 1px solid #eee;
            padding: 10px;
            min-height: 100px;
        }
        .grid-item.span-3 {
            grid-column: span 3;
        }
        h1 {
            text-align: center;
            margin-bottom: 20px;
        }
        h2 {
            font-size: 1.2em;
            margin-bottom: 5px;
            color: #333;
        }
        p {
            font-size: 0.9em;
            color: #555;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Business Model Canvas - {{ $businessPlanId }}</h1>

        <div class="grid-container">
            <!-- Key Partners -->
            <div class="grid-item">
                <h2>Key Partners</h2>
                <p>{{ $canvasData['key_partners'] ?? 'N/A' }}</p>
            </div>

            <!-- Key Activities -->
            <div class="grid-item">
                <h2>Key Activities</h2>
                <p>{{ $canvasData['key_activities'] ?? 'N/A' }}</p>
            </div>

            <!-- Key Resources -->
            <div class="grid-item">
                <h2>Key Resources</h2>
                <p>{{ $canvasData['key_resources'] ?? 'N/A' }}</p>
            </div>

            <!-- Value Propositions -->
            <div class="grid-item span-3">
                <h2>Value Propositions</h2>
                <p>{{ $canvasData['value_propositions'] ?? 'N/A' }}</p>
            </div>

            <!-- Customer Relationships -->
            <div class="grid-item">
                <h2>Customer Relationships</h2>
                <p>{{ $canvasData['customer_relationships'] ?? 'N/A' }}</p>
            </div>

            <!-- Channels -->
            <div class="grid-item">
                <h2>Channels</h2>
                <p>{{ $canvasData['channels'] ?? 'N/A' }}</p>
            </div>

            <!-- Customer Segments -->
            <div class="grid-item">
                <h2>Customer Segments</h2>
                <p>{{ $canvasData['customer_segments'] ?? 'N/A' }}</p>
            </div>

            <!-- Cost Structure -->
            <div class="grid-item span-3">
                <h2>Cost Structure</h2>
                <p>{{ $canvasData['cost_structure'] ?? 'N/A' }}</p>
            </div>

            <!-- Revenue Streams -->
            <div class="grid-item">
                <h2>Revenue Streams</h2>
                <p>{{ $canvasData['revenue_streams'] ?? 'N/A' }}</p>
            </div>
        </div>
    </div>
</body>
</html>
