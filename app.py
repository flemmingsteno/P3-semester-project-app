import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import Input, Output, dcc, html
import pandas as pd
import plotly.express as px
from PIL import Image
import utm
import psycopg2
import datetime


class Database():
    """
    Represents and connects to the database. Retrieves data from database server.
    -------
    Attributes:
        connection_string : str
    -------
    Methods:
        get_table(self, query):
            Connects to the database server and loads data to a data frame
            according to the query parameter, which must be an SQL query in a string
            Returns data frame
    """
    def __init__(self, connection_string):
        self.connection_string = connection_string
    def get_table(self, query):
        self.conn = None
        try: 
            self.conn = psycopg2.connect(self.connection_string)
            self.tabel = pd.read_sql_query(query, self.conn)
            self.tabel["customdata"] = self.tabel.index   # "customdata" is used to filter data when selecting data points
            self.conn.close()
            return self.tabel
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if self.conn is not None:
                self.conn.close()
        
        
database = Database("host='p3-database-do-user-10084776-0.b.db.ondigitalocean.com' port='25060' dbname='windturbines' user='doadmin' password='2tEAWu2uT4xWVLWj'")

                                                                  
class Plot():
    """
    Factory class for creating and updating a plotly express object.
    Functions as a template for sub-classes.
    -------
    Methods:
        get_df(self, query):
            Uses the Database class to retrieve data from database server.
            query must be a string with a SQL query.
            Returns data frame
        update_plot(self, selected_plot):
            Updates the data that the plotly express object uses according
            to the selected points.
            Returns plotly express object as self.fig.
    """
    def get_df(self, query):
        return database.get_table(query)
    #def fill_plot(self):
    def update_plot(self, selectedpoints):
        selected_points = pd.DataFrame(selectedpoints, columns = ["customdata"])
        updated_df = pd.merge(self.df, selected_points, how = "inner", on="customdata")   # Filter data by using the "customdata" column
        if isinstance(self, Scatter_plot):   # Test type of self
            self.fig = px.scatter(data_frame = updated_df, x = self.x,
                       y = self.y, color = self.group,
                       labels = {self.x: self.x_lab,
                                 self.y: self.y_lab},
                       title = self.title,
                       template = "simple_white",
                       custom_data = ["customdata"],
                       color_discrete_sequence = ["green", "red", "blue", "brown", "purple"],
                       category_orders = {"region": ["NJ", "MJ", "SJ", "FU", "ZL"]}
                       ).update_layout(dragmode='select')
            return self.fig
        else:
            self.fig = px.violin(data_frame = updated_df,
                         x = self.x,
                         y = self.y,
                         color = self.x,
                         labels = {self.x: self.x_lab,
                                   self.y: self.y_lab},
                         title = self.title,
                         template = "simple_white",
                         box = True,
                         color_discrete_sequence = ["green", "red", "blue", "brown", "purple"],
                         category_orders = {"region": ["NJ", "MJ", "SJ", "FU", "ZL"]}
                         ).update_layout(dragmode='select')
            return self.fig


class Histogram_plot(Plot):
    """
    Represents a histogram plot. Inherits from Plot class.
    -------
    Attributes:
        x : str
            the x-variable
        x_lab : str
            label on x-axis
        title : str
            title of plot
        binwidth : int
            the width of each bin
        group : str
            The attribute is optional (default = False). The varible to group the histogram by.
    -------
    Methods:
        fill_plot(self, query):
            Fills plot with data and visualizes a histogram.
            query must be a string with a SQL query.
            Returns plotly express object as self.fig 
    """
    def __init__(self, x, x_lab, title, binwidth, group=False):
        self.x = x
        self.x_lab = x_lab
        self.title = title
        self.binwidth = binwidth
        self.group = group
    def fill_plot(self, query):
        self.df = self.get_df(query)
        self.df.dropna(subset = ["efficiency", "region"], inplace=True)   # Delete rows where an element is NA
        if not self.group:
            self.fig = px.histogram(data_frame = self.df, x = self.x,
                                labels = {self.x: self.x_lab,
                                          "count": "Count"},
                                title = self.title,
                                template = "simple_white",
                                nbins = int((max(self.df[self.x])-min(self.df[self.x]))/self.binwidth),
                                color_discrete_sequence=['darkblue']).update_layout(
                                    yaxis_title="Count")
            return self.fig
        else:
            self.fig = px.histogram(data_frame = self.df, x = self.x,
                                color = self.group,
                                labels = {self.x: self.x_lab,
                                          "count": "Count"},
                                title = self.title,
                                template = "simple_white",
                                nbins = int((max(self.df[self.x])-min(self.df[self.x]))/self.binwidth),   # Determine number of bins from self.binwidth
                                color_discrete_sequence = ["green", "red", "blue", "brown", "purple"],
                                category_orders = {"region": ["NJ", "MJ", "SJ", "FU", "ZL"]}
                                ).update_layout(
                                    yaxis_title="Count")
            return self.fig



class Scatter_plot(Plot):
    """
    Represents a scatter plot. Inherits from Plot class.
    -------
    Attributes:
        x : str
            the x-variable
        x_lab : str
            label on x-axis
        y : str
            the y-variable
        y_lab : str
            label on y-axis
        title : str
            title of plot
        derive : boolean
            the attribute is optional (default = False). If True,
            a specified variable will be derived.
        operation : str
            the attribute is optional (default = False). Specific string
            identifying the operation which will be used to derive a specific variable.
        group : str
            the attribute is optional (default = False). The varible to group the scatter plot by.
    -------
    Methods:
        fill_plot(self, query):
            Fills plot with data according to the attributes and visualizes a scatter plot.
            query must be a string with a SQL query.
            Returns plotly express object as self.fig 
    """
    def __init__(self, x, x_lab, y, y_lab, title, derive=False, operation=False, group=False):
        self.x = x
        self.x_lab = x_lab
        self.y_lab = y_lab
        self.title = title
        self.y = y
        self.derive = derive
        self.operation = operation
        self.group = group
    def fill_plot(self, query):
        self.df = self.get_df(query)
        if not self.derive:
            if not self.group:
                self.fig = px.scatter(data_frame = self.df, x = self.x,
                                   y = self.y,
                                   labels = {self.x: self.x_lab,
                                             self.y: self.y_lab},
                                   title = self.title,
                                   template = "simple_white",
                                   color_discrete_sequence=['darkblue'])
                return self.fig
            elif self.group != "region":
                self.df.dropna(subset = [self.group, self.x, self.y], inplace=True)   # Delete rows where an element is NA
                self.fig = px.scatter(data_frame = self.df, x = self.x,
                   y = self.y, color = self.group,
                   labels = {self.x: self.x_lab,
                             self.y: self.y_lab},
                   title = self.title,
                   template = "simple_white",
                   custom_data = ["customdata"]).update_layout(dragmode='select')
                return self.fig
            else:
                self.df.dropna(subset = [self.group, self.x, self.y], inplace=True)   # Delete rows where an element is NA
                self.fig = px.scatter(data_frame = self.df, x = self.x,
                   y = self.y, color = self.group,
                   labels = {self.x: self.x_lab,
                             self.y: self.y_lab},
                   title = self.title,
                   template = "simple_white",
                   custom_data = ["customdata"],
                   color_discrete_sequence = ["green", "red", "blue", "brown", "purple"],
                   category_orders = {"region": ["NJ", "MJ", "SJ", "FU", "ZL"]}
                   ).update_layout(dragmode='select')
                return self.fig
        else:
            self.derived_df = Derive_variable(self.df, self.operation).derive()
            if not self.group:
                self.fig = px.scatter(data_frame = self.derived_df, x = self.x,
                                   y = self.y,
                                   labels = {self.x: self.x_lab,
                                             self.y: self.y_lab},
                                   title = self.title,
                                   template = "simple_white",
                                   color_discrete_sequence=['darkblue']
                                   ).update_traces(mode='lines+markers')   # Add lines between points
                return self.fig
            else:
                self.fig = px.scatter(data_frame = self.derived_df, x = self.x,
                   y = self.y, color = self.group,
                   labels = {self.x: self.x_lab,
                             self.y: self.y_lab},
                   title = self.title,
                   template = "simple_white")
                return self.fig


class Derive_variable():
    """
    Determines a derived variable. It either derives number of active
    wind turbines in each year or derives the total power production
    in each year.
    -------
    Attributes:
        df : data frame
            Data frame with the data for deriving the variable.
        operation : str
            Uniqe string identifying the derived variable.
    Methods:
        derive(self):
            Determines the values for the derived variable for each row in 
            self.df and loads them into the data frame in a new column.
            Returns the new data frame.
    """
    def __init__(self, df, operation):
        self.df = df
        self.operation = operation
    def derive(self):
        if self.operation == "active_turbines":
            template = {"Year": [datetime.date(year, 1, 1) for year in range(1977, 2021)], "n": [0]*44}   # "Year"-elements is a datatime object. Year range from 1977 to 2021
            for y in range(len(template["Year"])):
                for index in range(len(self.df["date_of_connection"])):
                    if self.df["date_of_connection"][index] <= template["Year"][y]:   # Test if wind turbine was connected before the current year in the outer for-loop
                        if self.df["date_of_decommission"][index] == None:
                           template["n"][y] += 1
                        elif self.df["date_of_decommission"][index] >= template["Year"][y]:
                            template["n"][y] += 1
            self.new_df = pd.DataFrame.from_dict(data=template)
            return self.new_df
        elif self.operation == "production":
            template = {"Year": [year for year in range(1977,2021)], "Production": [0]*44}   # Create dictionary with Year column and production column
            index_dict = {}   # Create index dictionary to improve performance
            keys = [year for year in range(1977,2021)]
            values = [i for i in range(44)]
            for i in values:   # Fill index_dictionary with an index for each year
                index_dict[keys[i]] = i
            
            for year in range(len(self.df["year"])):   # self.df["year"] is column with each year each wind turbine produced power
                index = index_dict[int(self.df["year"][year][1:])]   # self.df["year"][year][1:] is the year in which the kWh was produced
                template["Production"][index] += self.df["kwh"][year]   # Add the produced power to the current year in the iteration
            self.new_df = pd.DataFrame.from_dict(data=template)   # Convert dictionary to data frame
            self.new_df["Production"] = self.new_df["Production"]/1000000
            return self.new_df


class Violin_plot(Plot):
    """
    Represents a violin plot. Inherits from Plot class.
    -------
    Attributes:
        x : str
            the x-variable
        x_lab : str
            label on x-axis
        y : str
            the y-variable
        y_lab : str
            label on y-axis
        title : str
            title of plot
    -------
    Methods:
        fill_plot(self, query):
            Fills plot with data according to the attributes and visualizes a violin plot.
            query must be a string with a SQL query.
            Returns plotly express object as self.fig 
    """
    def __init__(self, x, x_lab, y, y_lab, title):
        self.x = x
        self.x_lab = x_lab
        self.y = y
        self.y_lab = y_lab
        self.title = title
    def fill_plot(self, query):
        self.df = self.get_df(query)
        self.df.dropna(subset = self.df.columns, inplace=True)   # Delete rows where an element is NA
        self.fig = px.violin(data_frame = self.df,
                         x = self.x,
                         y = self.y,
                         color = self.x,
                         labels = {self.x: self.x_lab,
                                   self.y: self.y_lab},
                         title = self.title,
                         template = "simple_white",
                         box = True,
                         color_discrete_sequence = ["green", "red", "blue", "brown", "purple"],
                         category_orders = {"region": ["NJ", "MJ", "SJ", "FU", "ZL"]},
                         custom_data = ["customdata"]).update_layout(dragmode='select').update_yaxes(range = [0,80])
        return self.fig

class Map_plot(Plot):
    """
    Represents a scatter plot with an image as background.
    -------
    Methods:
        fill_plot(self, query):
            Fills plot with data according to the attributes and visualizes
            a scatter plot with an image (map) as background.
            It filters the data for incorrect or dirty data and transforms
            the coordinates from utm to latitude and longitude.
            query must be a string with a SQL query.
            Returns plotly express object.
    """
    def fill_plot(self, query):
        self.df = self.get_df(query)
        background = Image.open('map.png')
        BBox = [7.39554279514701, 15.289272812025047, 54.27544003736202+0.035, 57.98745197773329+0.035]   # Border values for the map
        
        coord_utm = self.df[["x_coordinates", "y_coordinates"]]
        
        n_row = self.df.shape[0]
        x_utm = []
        y_utm = []
        efficiency = []
        for i in range(n_row):
            if coord_utm["x_coordinates"][i] > 100000 and coord_utm["x_coordinates"][i] < 999999 and self.df["efficiency"][i] > 1.0:
                # Only include coordinates for wind turbines with valid coordinates and efficiency.
                x_utm.append(coord_utm["x_coordinates"][i])
                y_utm.append(coord_utm["y_coordinates"][i])
                efficiency.append(self.df["efficiency"][i])
        
        x_lat = []
        y_lon = []
        for i in range(len(x_utm)):
            lat_lon = utm.to_latlon(x_utm[i], y_utm[i], zone_number = 32, northern = True)   # Convert utm coordinates to latitude, longitude
            x_lat.append(lat_lon[0])
            y_lon.append(lat_lon[1])

        coord_latlon = pd.DataFrame({"x_lat":x_lat, "y_lon":y_lon, "efficiency": efficiency})

        denmark_plot = px.scatter(data_frame = coord_latlon,
                                  x = "y_lon",
                                  y = "x_lat",
                                  color = "efficiency",
                                  opacity = 0.4,
                                  labels = {"y_lon": "x", "x_lat": "y", "efficiency": "efficiency"},
                                  width = 1000,
                                  height = 700,
                                  template = "simple_white",
                                  color_continuous_scale = "plasma"
                                  ).add_layout_image(
                            dict(
                                source=background,
                                xref="x",
                                yref="y",
                                x=BBox[0],
                                y=BBox[3],
                                sizex=BBox[1]-BBox[0],
                                sizey=BBox[3]-BBox[2],
                                sizing="stretch",
                                opacity=1,
                                layer="below")
                    )
        return denmark_plot


class Plots_set():
    """
    Represents a set of all plots. The plots can be accessed through a dictionary.
    -------
    Attributes:
        wind_turbines : Scatter_plot object
        power_production : Scatter_plot object
        hub_rot : Scatter_plot object
        cap_rot_hub : Scatter_plot object
        efficiency_hist : Histogram_plot object
        map1 : Map_plot object
        efficiency_violin : Violing_plot object
        capacity_efficiency : Scatter_plot object
    -------
    Methods:
        generate(self):
            The method calls the fill_plot method on all the attribute objects
            and stores them in a dictionary in self.plot_dictionary.
            Returns dictionary with plots.
    """
    def __init__(self):
        self.wind_turbines = Scatter_plot(x = "Year", x_lab = "Year", y = "n", y_lab = "Quantity", title = "Number of active wind turbines in each year", derive = True, operation = "active_turbines")
        self.power_production = Scatter_plot(x = "Year", x_lab = "Year", y = "Production", y_lab = "Production (GWH)", title = "Production in each year", derive = True, operation = "production")
        self.hub_rot = Scatter_plot(x = "hub_height", x_lab = "Hub Height (m)", y = "rotor_diameter", y_lab = "Rotor Diameter (m)", title = "Hub Height vs Rotor Diameter")
        self.cap_rot_hub = Scatter_plot(x = "capacity", x_lab = "Capacity (kW)", y = "rotor_diameter", y_lab = "Rotor Diameter (m)", title = "Correlation between size variables", group = "hub_height")
        self.efficiency_hist = Histogram_plot(x = "efficiency", x_lab = "Efficiency (%)", title = "Efficiency distribution", binwidth = 0.5, group = "region")
        self.map1 = Map_plot()
        self.efficiency_violin = Violin_plot(x = "region", x_lab = "Region", y = "efficiency", y_lab = "Efficiency (%)", title = "Efficiency by Region")
        self.capacity_efficiency = Scatter_plot(x = "capacity", x_lab = "Capacity (kW)", y = "efficiency", y_lab = "Efficiency (%)", title = "Capacity vs Efficiency", group = "region")
    def generate(self):
        self.plot_dictionary = {"active_turbines": self.wind_turbines.fill_plot("""
                                                        SELECT "date_of_connection", "date_of_decommission"
                                                        FROM "turbines"
                                                        """),
                "power_production": self.power_production.fill_plot("""
                                                            SELECT "year", "kwh"
                                                            FROM "power_year"
                                                            """),
                "hub_rot": self.hub_rot.fill_plot("""
                                          SELECT "hub_height", "rotor_diameter"
                                          FROM "turbine_characteristics"
                                          WHERE "hub_height">4 AND "rotor_diameter">0
                                          """),
                "cap_rot_hub": self.cap_rot_hub.fill_plot("""
                                                          SELECT "capacity", "rotor_diameter", "hub_height"
                                                          FROM "turbine_characteristics"
                                                          WHERE "capacity">5 and "rotor_diameter">0
                                                          """),
                "efficiency_hist": self.efficiency_hist.fill_plot("""
                                                        SELECT "efficiency", "region", e."turbine_id"
                                                        FROM "efficiency" AS e
                                                        FULL JOIN "turbines" AS t ON e."turbine_id"=t."turbine_id"
                                                        """),
                "efficiency_violin": self.efficiency_violin.fill_plot("""
                                                              SELECT "efficiency", "capacity", "region"
                                                              FROM "efficiency" AS e
                                                              FULL JOIN "turbine_characteristics" as t on e."turbine_id"=t."turbine_id"
                                                              FULL JOIN "turbines" AS t2 on e."turbine_id"=t2."turbine_id"
                                                              WHERE t."capacity">5
                                                              """),
                "map1": self.map1.fill_plot("""
                                    SELECT t."turbine_id", "efficiency", "x_coordinates", "y_coordinates"
                                    FROM "turbines" AS t
                                    FULL JOIN "efficiency" AS e ON e."turbine_id" = t."turbine_id"
                                    WHERE t."date_of_decommission" IS Null
                                    """),
                "capacity_efficiency": self.capacity_efficiency.fill_plot("""
                                                                  SELECT "efficiency", "capacity", "region"
                                                                  FROM "efficiency" AS e
                                                                  FULL JOIN "turbine_characteristics" as t on e."turbine_id"=t."turbine_id"
                                                                  FULL JOIN "turbines" AS t2 on e."turbine_id"=t2."turbine_id"
                                                                  WHERE t."capacity">5
                                                                  """)
                                    }
        return self.plot_dictionary

plots_object = Plots_set()
plot_dictionary = plots_object.generate()


# ===========App layout===========

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(
    [
        dcc.Store(id="store"),
        html.H1("Danish Wind Turbines"),
        html.Hr(),
        dbc.Button(
            "Regenerate graphs",
            color="primary",
            id="button",
            className="mb-3",
        ),
        dbc.Tabs(
            [
                dbc.Tab(label="Homepage", tab_id="homepage"),
                dbc.Tab(label="Relevance", tab_id="relevance"),
                dbc.Tab(label="Correlations", tab_id="correlations"),
                dbc.Tab(label="Location", tab_id="maps"),
                dbc.Tab(label="Capacity's affect on Efficiency", tab_id="capacity")
            ],
            id="tabs",
            active_tab="homepage",
        ),
        html.Div(id="tab-content", className="h-100"),
    ],
    style={"height": "100vh"},
)


# ===========App callbacks===========

@app.callback(
    Output("tab-content", "children"),
    [Input("tabs", "active_tab"), Input("store", "data")],
)
def render_tab_content(active_tab, data):
    """
    This callback takes the 'active_tab' property as input, as well as the
    stored graphs, and renders the tab content depending on what the value of
    'active_tab' is.
    """
    if active_tab and data is not None:
        if active_tab == "homepage":
            return [dcc.Markdown('''
                                 Welcome to the data visualization application made by group DV3-02.
                                 
                                 In the application you will find various figures that support the conlusion in the report.
                                 
                                 The problem statement from the report is as follows:
                                     
                                 Where in Denmark is the optimal location for a wind turbine and what should the dimensions be to achieve maximum efficiency when considering the dimensions capacity (kW), hub height (m) and rotor diameter (m)?
                                 
                                 * How do we measure efficiency?
                                 * Where to place wind turbines to get the biggest electricity production by coordinates?
                                 * How does capacity (kW) affect efficiency?
                                 * How can an interactive data visualization application help a user discover answers to the problem statement?
                                 
                                 The data is published by Energistyrelsen and was retrieved on the 6th of September 2021.
                                 ''')]
        elif active_tab == "relevance":
            return [dcc.Markdown('''
                                 Below you see two figures that shows the overall development in the wind turbine industry in Denmark from 1977 to 2020.
                                 '''),
                dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=data["active_turbines"]), width=6),
                    dbc.Col(dcc.Graph(figure=data["power_production"]), width=6)
                ]
                ),
                dcc.Markdown('''
                             On the figure to the left you see a steep increase in number of active wind turbines from 1977 to 2002. 
                             In the years around 2002 the danish government introduced a repowering program where they gave turbine manufacturers 
                             incentive to build bigger wind turbines than previously. The repowering program can be observed as the stagnation 
                             of the points after the year 2002.
                             
                             On the figure to the right you see a rapid increase in power production by wind turbines from 1996 to 2020.
                             It is interesting that the power production keeps increasing even when the number of active wind turbines is the same
                             or is decreasing. This indicates that the repowering program was successful, and more high-capacity wind turbines were 
                             built as many low-capacity wind turbines were decommissioned (disconnected from the power grid).
                             
                             In conclusion, the overall development of wind turbines in Denmark is positive. Wind turbines are getting bigger and more efficient 
                             which results in an increase of power production at a high rate.''')]
        elif active_tab == "correlations":
            return [dcc.Markdown('''
                                 Below you see two figures that shows the correlation between the size variables of active wind turbines.
                                 
                                 * Capacity: The size of the turbine in kW.
                                 * Rotor Diameter: The diameter of the surface area of the wings in meters.
                                 * Hub Height: The height of the turbine tower in meters.
                                 
                                 By observing the correlation between the size variables, it is possible to determine the independent variable.
                                 '''),
                    dbc.Row(
                        [
                        dbc.Col(dcc.Graph(figure=data["cap_rot_hub"]), width=6),
                        dbc.Col(dcc.Graph(figure=data["hub_rot"]), width=6)
                        ]),
                    dcc.Markdown('''
                                 In the figure to the left you can see the correlation between the three size variables. 
                                 It can be observed that the correlation between Capacity (kW) and Rotor Diameter (m) is not linear 
                                 and the same is the case of Hub Height (m). The correlation between Hub Height (m) and Capacity (kW)
                                 looks very similar to the points plotted, which can be seen by the smooth transitioning of the colors. 
                                 The similarity in correlations indicates that the correlation between Rotor Diameter (m) and Hub Height (m) is linear which can be seen
                                 in the figure to the right.
                                 
                                 Because of the fact that Rotor Diameter (m) and Hub Height (m) is not linearly correlated to Capacity (kW) suggests
                                 that Capacity (kW) could be the independant variable.''')
                ]
        elif active_tab == "maps":
            return [dcc.Markdown('''
                                 Below you see three figures that shows information about the location and efficency of wind turbines.
                                 
                                 In the figures it is possible to observe information regarding the optimal locations to get the most efficienct wind turbine.
                                 '''),
                dbc.Row([dbc.Col(dcc.Graph(figure=data["map1"]), width=9)],
                    className="h-75"),
                dcc.Markdown('''
                             In the map above it can be seen that wind turbines are located across the country. However, it can be seen that the 
                             efficiency varies from location to location. By zooming on the map and comparing areas it can be observed that 
                             the most efficienct wind turbines are located on the west coast, and more specifically many are located near the north west 
                             coast of Jutland. It can also be observed that offshore wind turbines are generally more efficienct than onshore wind turbines.
                             '''),
                dbc.Row([dbc.Col(dcc.Graph(figure=data["efficiency_hist"]), width=9)],
                    className="h-50"),
                dcc.Markdown('''
                             Now the distribution of efficiency across regions can be compared in the histogram above.
                             
                             The regions are named as:
                                 
                            * NJ: North Jutland
                            * MJ: Mid Jutland
                            * SJ: South Jutland
                            * FU: Funen
                            * ZL: Zealand
                            
                            By zooming and panning in the histogram, it can be seen that North Jutland and Mid Jutland have a big representation 
                            in the middle and upper part of the distribution. It looks as if the North Jutland has most wind turbines with a 
                            relativly high efficiency compared to the other regions. North Jutland is most represented in wind turbines with an 
                            efficiency greater than 46%.
                            '''),
                dbc.Row([dbc.Col(dcc.Graph(id = "eff_violin", figure=data["efficiency_violin"]), width=9),
                         dbc.Col(dcc.RadioItems(id = "radioitem",
                            options=[
                                {'label': 'All', 'value': 'all'},
                                {'label': 'Onshore', 'value': 'onshore'},
                                {'label': 'Offshore', 'value': 'offshore'}
                            ],
                            value='all',
                            labelStyle={'display': 'block'}
                        ))],
                    className="h-50"),
                dcc.Markdown('''
                             Now we can see the distribution of efficiency within each region and compare quartiles between regions. We can also 
                             compare the specific distribution, and see that the distribution of Zealand looks more spread than for example the distribution 
                             of Mid Jutland which has many wind turbines with an efficiency around 21%. However, Mid Jutland has many outliers as well. 
                             We see that North Jutland and Mid Jutland has the wind turbines with the highest max efficiency of around 71% and 77 % respectively.
                             
                             By choosing back and forth between the "All" and the "Onshore" options in the items on the right, you can see the effect that
                             offshore wind turbines have on the efficiency in each region. Notice how the interquartile range becomes much bigger in the
                             Zealand region and the South Jutland region when going from onshore turbines to all turbines.
                            ''')
                ]
        elif active_tab =="capacity":
            return [dcc.Markdown('''
                                 The two figures below shows information about the correlation between capacity, efficiency and location.
                                 
                                 The two figures are linked which means that you can select wind turbines in either of the figures and the other figure will show the corresponding wind turbines.
                                 
                                 If you want to reset the selection you can double click in the figure and all wind turbines will be shown again.
                                 '''),
                dbc.Row([dbc.Col(dcc.Graph(id="cap_eff_plot", figure=data["capacity_efficiency"]), width=9)],
                        className="h-50"),
                dbc.Row([dbc.Col(dcc.Graph(id="eff_violin_plot2", figure=data["efficiency_violin"]), width=9)],
                        className="h-50"),
                dcc.Markdown('''
                             In the figure at the top, you see the correlation between the Capacity (kW) and efficency % grouped by region. As observed in the histogram 
                             in the Location tab, many wind turbines have an efficiency of around 21 %. It can be seen that higher Capacity (kW) 
                             does not equal a higher efficiency.
                             We see a lot of low-capacity wind turbines with a capacity below 25 kW; these wind turbines are called household wind turbines. 
                             The household wind turbines have a very wide spread efficiency from aroud 2% to around 77%. These wind turbines are not perticularly
                             interesting in regards to future wind turbines location because private people cannot choose where in the country they deploy
                             the wind turbine.
                             ''')
                ]
    return "No tab selected"


@app.callback(Output("store", "data"), [Input("button", "n_clicks")])
def generate_graphs(n):
    """
    This callback gets all the figures from global variable with dictionary of
    plots. It takes the "n_clicks" as input.
    Returns dictionary with plots. If the "Generate graphs" button is not
    clicked. Empty graphs will be shown.
    """
    if not n:
        # Generate empty graphs when app loads
        return {k: go.Figure(data=[]) for k in ["active_turbines", "power_production", "hub_rot", "cap_rot_hub", "efficiency_hist", "map1", "efficiency_violin", "capacity_efficiency"]}
    
    # Send plot dictionary to the dcc.Store
    return plot_dictionary

                                                    
@app.callback(
    Output("cap_eff_plot", "figure"),
    Output("eff_violin_plot2", "figure"),
    Input("cap_eff_plot", "selectedData"),
    Input("eff_violin_plot2", "selectedData")
    )
def update(selection1, selection2):
    """
    This callback updates the the capacity vs efficiency scatter plot and the
    efficiency histogram plot. It takes the "selecetedData" properties from
    the two graphs as inpupt.
    Returns updated plots.
    """
    if selection1:
        selected_points = [p["customdata"] for p in selection1["points"]]
    elif selection2:
        selected_points = [p["customdata"] for p in selection2["points"]]
    else:
        selected_points = plots_object.capacity_efficiency.df["customdata"]
    # Send the two updated figures back to dash layout part
    return [plots_object.capacity_efficiency.update_plot(selected_points),
            plots_object.efficiency_violin.update_plot(selected_points)]


@app.callback(
    Output("eff_violin", "figure"),
    Input("radioitem", "value")
    )
def update_radio(value):
    """
    This callback changes the violin plot to include all wind turbines, only onshore
    wind turbines, or only offshore wind turbines. It takes the the 'value'
    property of the radioitem component as input.
    Returns violin plot to figure of component with id='eff_violin'.
    """
    if value == "all":
        return plots_object.efficiency_violin.fill_plot("""
                                                        SELECT "efficiency", "capacity", "region"
                                                        FROM "efficiency" AS e
                                                        FULL JOIN "turbine_characteristics" as t on e."turbine_id"=t."turbine_id"
                                                        FULL JOIN "turbines" AS t2 on e."turbine_id"=t2."turbine_id"
                                                        WHERE t."capacity">5
                                                        """)
    elif value == "onshore":
        return plots_object.efficiency_violin.fill_plot("""
                                                        SELECT "efficiency", "region"
                                                        FROM "efficiency" AS e
                                                        FULL JOIN "turbine_characteristics" as t on e."turbine_id"=t."turbine_id"
                                                        FULL JOIN "turbines" AS t2 on e."turbine_id"=t2."turbine_id"
                                                        FULL JOIN "location" AS l ON e."turbine_id"=l."turbine_id"
                                                        WHERE t."capacity">5 AND l."type_of_location"='Land'
                                                        """)
    else:
        return plots_object.efficiency_violin.fill_plot("""
                                                        SELECT "efficiency", "region"
                                                        FROM "efficiency" AS e
                                                        FULL JOIN "turbine_characteristics" as t on e."turbine_id"=t."turbine_id"
                                                        FULL JOIN "turbines" AS t2 on e."turbine_id"=t2."turbine_id"
                                                        FULL JOIN "location" AS l ON e."turbine_id"=l."turbine_id"
                                                        WHERE t."capacity">5 AND l."type_of_location"='Hav'
                                                        """)

if __name__ == "__main__":
    app.run_server(debug=True, port=8888)