import matplotlib.pyplot as plt

def plot_portfolio(report):
    if not report:
        print("No data to plot")
        return
    
    names = list(report.keys())
    values = list(report.values())
    
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(names, values, color=['#1f77b4', '#ff7f0e'])
    ax.set_title('Current Portfolio Value')
    ax.set_ylabel('Value (₹)')
    ax.tick_params(axis='x', rotation=15)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'₹{height:,.0f}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('data/current_portfolio.png', dpi=150)
    plt.show()