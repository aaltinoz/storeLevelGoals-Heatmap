import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

"""
USER SHOULD INPUT CONVERSION AND TRAFFIC CSV BEFORE RUNNING PROGRAM
"""


# input conversion.csv
# conversion = pd.read_csv(sep=',')
#input traffic.csv
# traffic = pd.read_csv(sep=',')


# Get Min&Max Dates for conversion csv
CONV_START_DATE = pd.to_datetime(conversion['publish_time']).dt.normalize().min().date().strftime('%m-%d-%y')
CONV_END_DATE = pd.to_datetime(conversion['publish_time']).dt.normalize().max().date().strftime('%m-%d-%y')

# Get Min&Max Dates for conversion csv
TRAFF_START_DATE = pd.to_datetime(traffic['publish_time']).dt.normalize().min().date().strftime('%m-%d-%y')
TRAFF_END_DATE = pd.to_datetime(traffic['publish_time']).dt.normalize().max().date().strftime('%m-%d-%y')


def count_weekdays(datetime):
    # Define the order of weekdays
    order_of_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # Get the weekday names for each date in the DateTimeIndex
    weekdays = pd.to_datetime(datetime).day_name()

    # Use value_counts to count the occurrences of each weekday
    day_counts_unsorted = weekdays.value_counts().to_dict()

    # Sort the dictionary based on the order of weekdays and filter out zeros
    day_counts = {day: day_counts_unsorted.get(day, 0) for day in order_of_days if day_counts_unsorted.get(day, 0) != 0}

    return day_counts

def tweak_conversion_traffic(conversion,traffic):
  # Day Mapping
  day_mapping = {
      1: 'Monday',
      2: 'Tuesday',
      3: 'Wednesday',
      4: 'Thursday',
      5: 'Friday',
      6: 'Saturday',
      7: 'Sunday'
  }


  # preprocess for conversion
  conversion.index = pd.to_datetime(conversion['publish_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
  conversion['Date_conv'] = pd.to_datetime(conversion['publish_time']).dt.strftime('%m/%d/%Y').dropna()
  conversion = conversion.rename(columns={'hour': 'hour_conv',
                                          'day': 'day_conv'})
  conversion['Sales'] = conversion.iloc[:, 8]
  conversion['Orders'] = conversion.iloc[:, 16]
  conversion['Order Items'] = conversion.iloc[:, 22]
  conversion=conversion.dropna()

  #Create conv_data
  conv_data = conversion.groupby(['hour_conv','day_conv']).sum(numeric_only=True).reset_index()
  conv_data = conv_data[['hour_conv','day_conv','Sales','Orders','Order Items']]
  # Get encoded days
  conv_data['encoded_days_conv'] = conv_data['day_conv'].map(day_mapping)
  conv_data['daytime_encode'] = conv_data['hour_conv'].astype(int).astype(str) + '-' + conv_data['day_conv'].astype(int).astype(str)
  # preprocess for traffic
  traffic.index = pd.to_datetime(traffic['publish_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
  traffic['Date_traffic'] = pd.to_datetime(traffic['publish_time']).dt.strftime('%m/%d/%Y').dropna()
  traffic = traffic.rename(columns={'impressions':'Impressions',
                                    'clicks': 'Clicks',
                                    'cost': 'Cost',
                                    'hour': 'hour_traffic',
                                    'day': 'day_traffic'})
  traffic = traffic.dropna()

  # Get traffic data
  traffic_data = traffic.groupby(['hour_traffic','day_traffic']).sum(numeric_only=True).reset_index()
  traffic_data = traffic_data[['hour_traffic','day_traffic','Cost','Impressions','Clicks']]
  # Get encoded days
  traffic_data['encoded_days_traffic'] = traffic_data['day_traffic'].map(day_mapping)
  traffic_data['daytime_encode'] = traffic_data['hour_traffic'].astype(int).astype(str) + '-' + traffic_data['day_traffic'].astype(int).astype(str)

  # Get day_counts
  conversion_day_counts = count_weekdays(np.unique(conversion['Date_conv']))
  traffic_day_counts = count_weekdays(np.unique(traffic['Date_traffic']))

  # Add day_counts column
  conv_data['day_counts_conv'] = conv_data['encoded_days_conv'].map(conversion_day_counts)
  traffic_data['day_counts_traffic'] = traffic_data['encoded_days_traffic'].map(traffic_day_counts)

  # Add day_means of metrics
  #for convdata
  conv_data=conv_data.assign(mean_Sales=(conv_data['Sales']/conv_data['day_counts_conv']),
                  mean_Orders=(conv_data['Orders']/conv_data['day_counts_conv']),
                  mean_Order_Items=(conv_data['Order Items']/conv_data['day_counts_conv']))

  #for traffic data
  traffic_data=traffic_data.assign(mean_Cost=(traffic_data['Cost']/traffic_data['day_counts_traffic']),
                  mean_Impressions=(traffic_data['Impressions']/traffic_data['day_counts_traffic']),
                  mean_Clicks=(traffic_data['Clicks']/traffic_data['day_counts_traffic']))

  # Merge data
  merged_data = conv_data.merge(traffic_data, on='daytime_encode',how='left').fillna(0)
  merged_data = (merged_data.assign(\
          CVR = (merged_data['mean_Orders'] / merged_data['mean_Clicks']),
          CTR = (merged_data['Clicks'] / merged_data['Impressions']).fillna(0),
          AOV = (merged_data['Sales'] / merged_data['Orders']).fillna(0),
          ACOS = (merged_data['Cost'] / merged_data['Sales']).fillna(0)))
  merged_data['CVR'] = [0 if i == np.inf else np.round(i,2) for i in merged_data['CVR']]
  return  merged_data

# Apply function to create merged_data DataFrame
merged_data = tweak_conversion_traffic(conversion,traffic)


storeLevelGoals = ['Awareness', 'Consideration', 'Sales', 'Profit']

def get_storeGoal_heatmaps():


   
    while True:
        # Displaying the items for the user
        print("Please select an item from the Store Goals list:")
        for i, item in enumerate(storeLevelGoals, 1):  # Using enumerate to get index starting from 1
            print(f"{i}. {item}")  # Corrected this line to print each item

        # Get the user's choice
        choice = input("Enter the number of your choice (or 'exit' to quit): ")

        # Allow user to exit the loop
        if choice.lower() == 'exit':
            break

        # Ensure the choice is an integer and then check if it's valid
        try:
            choice = int(choice)
            if 1 <= choice <= len(storeLevelGoals):
                storeGoal = storeLevelGoals[choice - 1]  # Subtracting 1 because list indices start at 0
                print(f"You selected: {storeGoal}")
                break
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a valid number or 'exit' to quit.")


    fig = None

    if storeGoal == 'Awareness':
        mainMetric='mean_Impressions'
        ruleMetric_2 = 'CTR'
        plot_title='Impressions'
        START_DATE = TRAFF_START_DATE
        END_DATE = TRAFF_END_DATE
        plot_data = merged_data[merged_data.day_traffic != 0].pivot_table(index = 'hour_traffic', columns = 'day_traffic',
                                                                            values = mainMetric,
                                                                            aggfunc = 'sum').fillna(0)

        # Get interquantiles for query
        mainQuantile = np.percentile(merged_data[merged_data.day_traffic != 0]['mean_Impressions'],75)
        rule2Quantile = np.percentile(merged_data[merged_data.day_traffic != 0]['CTR'],50)

        radartackled = merged_data.query(f'{mainMetric} < {mainQuantile} & {ruleMetric_2} > {rule2Quantile}')['daytime_encode'].tolist()

    
    elif storeGoal == 'Consideration':
        mainMetric='mean_Clicks'
        ruleMetric_2 = 'CTR'
        plot_title='Clicks'
        START_DATE = TRAFF_START_DATE
        END_DATE = TRAFF_END_DATE
        plot_data = merged_data[merged_data.day_traffic != 0].pivot_table(index = 'hour_traffic', columns = 'day_traffic',
                                                                            values = mainMetric,
                                                                            aggfunc = 'sum').fillna(0)

        # Get interquantiles for query
        mainQuantile = np.percentile(merged_data[merged_data.day_traffic != 0][f'{mainMetric}'],75)
        rule2Quantile = np.percentile(merged_data[merged_data.day_traffic != 0][f'{ruleMetric_2}'],50)

        radartackled = merged_data.query(f'{mainMetric} < {mainQuantile} & {ruleMetric_2} > {rule2Quantile}')['daytime_encode'].tolist()
    
    elif storeGoal == 'Sales':
        mainMetric='mean_Sales'
        ruleMetric_2 = 'CVR'
        plot_title='Sales'
        START_DATE = CONV_START_DATE
        END_DATE = CONV_END_DATE
        plot_data = merged_data[merged_data.day_traffic != 0].pivot_table(index = 'hour_traffic', columns = 'day_traffic',
                                                                            values = mainMetric,
                                                                            aggfunc = 'sum').fillna(0)

        # Get interquantiles for query
        mainQuantile = np.percentile(merged_data[merged_data.day_traffic != 0][f'{mainMetric}'],75)
        rule2Quantile = np.percentile(merged_data[merged_data.day_traffic != 0][f'{ruleMetric_2}'],50)

        radartackled = merged_data.query(f'{mainMetric} < {mainQuantile} & {ruleMetric_2} > {rule2Quantile}')['daytime_encode'].tolist()
    
    elif storeGoal == 'Profit':
        mainMetric='mean_Sales'
        ruleMetric_2 = 'CVR'
        ruleMetric_3 = 'ACOS'
        plot_title='Sales'
        START_DATE = CONV_START_DATE
        END_DATE = CONV_END_DATE
        plot_data = merged_data[merged_data.day_traffic != 0].pivot_table(index = 'hour_traffic', columns = 'day_traffic',
                                                                            values = mainMetric,
                                                                            aggfunc = 'sum').fillna(0)

        # Get interquantiles for query
        mainQuantile = np.percentile(merged_data[merged_data.day_traffic != 0][f'{mainMetric}'],75)
        rule2Quantile = np.percentile(merged_data[merged_data.day_traffic != 0][f'{ruleMetric_2}'],50)
        rule3Quantile = np.percentile(merged_data[merged_data.day_traffic != 0][f'{ruleMetric_3}'],50)

        radartackled = merged_data.query(f'{mainMetric} < {mainQuantile} & {ruleMetric_2} > {rule2Quantile} & {ruleMetric_3} < {rule3Quantile}')['daytime_encode'].tolist()



    # Create a heatmap without annotations
    fig, axes = plt.subplots(1, 2, figsize=(20, 15))

    # First heatmap
    sns.heatmap(plot_data, annot=True, fmt=".2f", cmap='Greens', cbar=True, ax=axes[0]).set(title=f'{plot_title} Heatmap for Store Goal: {storeGoal} {START_DATE} // {END_DATE}')

    # Annotations for the first heatmap
    for i in range( plot_data.shape[0]):
        for j in range(1,plot_data.shape[1]+1):
            if str(i) + '-' + str(j) in radartackled:
                axes[0].text(j-0.5 , i+0.5 , f'{plot_data.iloc[i, j-1]:.2f}',
                            ha='center', va='center', color='red')

    # Fix the tick labels for the first heatmap
    y_labels = [int(float(label.get_text())) for label in axes[0].get_yticklabels()]
    x_labels = [int(float(label.get_text())) for label in axes[0].get_xticklabels()]
    axes[0].set_xticklabels(x_labels)
    axes[0].set_yticklabels(y_labels)
    axes[0].invert_yaxis()

    # Second heatmap
    sns.heatmap(merged_data[merged_data.day_traffic != 0].pivot_table(index='hour_traffic', columns='day_traffic', values='CTR',aggfunc='sum').fillna(0),
            cmap='Greens', annot=True, ax=axes[1]).set(title=f'{ruleMetric_2}')
    y_labels = [int(float(label.get_text())) for label in axes[0].get_yticklabels()]
    x_labels = [int(float(label.get_text())) for label in axes[0].get_xticklabels()]
    axes[1].set_xticklabels(x_labels)
    axes[1].set_yticklabels(y_labels)
    axes[1].invert_yaxis()

    if fig:
        plt.tight_layout()
        plt.show()
    return fig

# Run Function
get_storeGoal_heatmaps()

