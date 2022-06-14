import os
import pandas as pd
import numpy as np

# Classifiers
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn import svm
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
import xgboost as xgb
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
# from sklearn.gaussian_process import GaussianProcessClassifier
# from sklearn.gaussian_process.kernels import RBF

# Analysis
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay
from sklearn.decomposition import PCA

def make_dataframe(dir):
    files = os.listdir(dir)

    # Looking for training data
    for file in files:
        if file.startswith("Dot") & file.endswith(".csv"):
            target_file = file
            print(f"File: {dir}{target_file}")
    
    # Checking if there is a suitable
    try:
        target_file
    except:
        print(f"Error: Failed to find file in:{dir}")
        exit()

    # Reducing dataframe size
    df = pd.DataFrame()
    df = pd.read_csv(f"{dir}{target_file}")

    # Reduce size of dataframe
    # temp = {i: np.float16 if i!="Data_Label" else object for i in df.dtypes.keys()}
    # df = pd.read_csv(f"{dir}{target_file}",dtype=temp)
    return df

def make_sensor_list(sensors):
    sensors = list(np.array(sensors)-1)
    sensors_list = []

    for ii in sensors:
        for jj in range(4):
            sensors_list.append(ii*4+jj)
    
    return sensors_list

class classify:
    def __init__(self, sensor_list):
        self.df_training = make_dataframe("Training Data/")
        self.classifiers = {
            "Random Forest": None,
            "Linear SVM": None,
            "RBF SVM": None,
            # "AdaBoost": None,
            "GuassianNB": None,
            "XG Boost": None,
            # "Gaussian Process": None,
            "KNN": None,
            "Neural Network": None,
            "QD Analysis": None,
            }
        self.results = self.classifiers.copy()
        self.accuracy_results = self.classifiers.copy()
        self.the_classifier = None
        self.testing_label = None
        self.testing_label_xgb = None
        self.labels = [chr(ii+65) for ii in range(9)]
        self.labels_xgb = list(np.arange(0, 8+1))
        self.sensor_list = sensor_list

    def make_model(self, input):
        # Training data
        training_data = self.df_training.iloc[:, make_sensor_list(self.sensor_list)].values
        training_label = self.df_training.iloc[:, 20].values

        print("Sensors:")
        print(list((self.df_training.iloc[:1, make_sensor_list(self.sensor_list)]).columns))
        # print(type(df_training))

        # Gaussian Process data
        # df_training_small = df_training.sample(frac = 0.1)
        # training_data_small = df_training_small.iloc[:, :20].values
        # training_label_small = df_training_small.iloc[:, 20].values

        # Classification
        if input == "all":
            print("Making ALL classifiers")

            # Random forest
            self.classifiers["Random Forest"] = RandomForestClassifier(max_depth = 5, n_estimators = 10, max_features=20).fit(training_data, training_label)

            # SVC
            self.classifiers["Linear SVM"] = svm.SVC(kernel="linear", C=0.01).fit(training_data, training_label)
            self.classifiers["RBF SVM"] = svm.SVC(gamma=2, C=1).fit(training_data, training_label)

            # AdaBoost
            # self.classifiers["AdaBoost"] = AdaBoostClassifier().fit(training_data, training_label)

            # Naive Bayes
            self.classifiers["GuassianNB"] = GaussianNB().fit(training_data, training_label)

            # XG Boost
            training_label_num = [self.labels.index(i) for i in training_label]
            self.classifiers["XG Boost"] = xgb.XGBClassifier()
            self.classifiers["XG Boost"].fit(training_data, training_label_num)

            # Gaussian process
            # self.classifiers["Gaussian Process"] = GaussianProcessClassifier(1.0 * RBF(1.0))
            # self.classifiers["Gaussian Process"].fit(training_data_small, training_label_small)

            # KNN
            self.classifiers["KNN"] = KNeighborsClassifier(3).fit(training_data, training_label)

            # Neural Network
            self.classifiers["Neural Network"] = MLPClassifier(alpha=1, max_iter=1000).fit(training_data, training_label)

            # QD Analysis
            self.classifiers["QD Analysis"] = QuadraticDiscriminantAnalysis().fit(training_data, training_label)
        elif input == "one":
            # SVC
            self.classifiers["Linear SVM"] = svm.SVC(kernel="linear", C=0.01).fit(training_data, training_label)
        else:
            self.the_classifier = svm.SVC(kernel="linear", C=0.01).fit(training_data, training_label)

    def test_model(self):
        print("Testing models")
        testing_dir = "Testing Data/"
        
        # Testing data
        df_testing = make_dataframe(testing_dir)
        testing_data = df_testing.iloc[:, make_sensor_list(self.sensor_list)].values
        self.testing_label = df_testing.iloc[:, 20].values
        
        # Converts chr to int
        self.testing_label_xgb = pd.DataFrame([self.labels.index(i) for i in self.testing_label])

        # Prediction
        for classifier in list(self.classifiers.keys()):
            if self.classifiers[classifier] is not None:
                pred = self.classifiers[classifier].predict(testing_data)
                
                # Changing testing label for special case
                testing_label = self.testing_label if classifier != "XG Boost" else self.testing_label_xgb

                # Accuracy
                self.accuracy_results[classifier] = accuracy_score(testing_label, pred)
                print(f"{classifier} Accuracy: {round(100 * (self.accuracy_results[classifier]), 2)}%")

                self.results[classifier] = pred
    
    def display_confusion_matrix(self):
        print("displaying models")
        # Changing the label type
        for classifier in list(self.classifiers.keys()):
            if self.classifiers[classifier] is not None:            
                if classifier != "XG Boost":
                    testing_label = self.testing_label
                    label = self.labels
                else:
                    testing_label = self.testing_label_xgb
                    label = self.labels_xgb
                
                disp = ConfusionMatrixDisplay.from_predictions(testing_label, self.results[classifier], labels = label, normalize = "true")
                disp.ax_.set_title(classifier)

                disp.ax_.text(
                    8,
                    9.7,
                    (f"Sensors: {self.sensor_list}      "+"Accuracy: "+str(round(self.accuracy_results[classifier], 3))).lstrip("0"),
                    size=19,
                    horizontalalignment="right",
                )
    
    def display_data_3D_plot(self):
        ax = plt.axes(projection='3d')

        # Training data
        # Quat
        # quat_data = self.df_training.iloc[:, 1:4].values.transpose()
        quat_data = self.df_training.iloc[:, make_sensor_list(self.sensor_list)[1:]].values.transpose()

        #Euler
        # quat_data = self.df_training.iloc[:, :4]
        # euler_data = [list(Quaternion(*i).to_euler(degrees = True)) for i in list(quat_data.values)]
        # euler_data = [list(Quaternion(*i)) for i in (list(quat_data.values))]
        # euler_data_T = np.array(euler_data).transpose()

        # Training label
        training_label = self.df_training.iloc[:, 20].values
        training_label_num = [self.labels.index(i) for i in training_label]
        
        ax.scatter3D(*reversed(quat_data), s = 2, c=training_label_num, cmap="brg")

        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        # ax.set_xlim(-180, 180)
        # ax.set_ylim(-180, 180)
        # ax.set_zlim(-180, 180)
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.set_zlim(-1, 1)
    
    def visualise_data(self):
        for ii in self.labels:
            # Removing other positions
            quat_data_trim = self.df_training[self.df_training.Data_Label == ii]
            
            # Removing other sensors
            quat_data = quat_data_trim.iloc[:, make_sensor_list(self.sensor_list)[1:]]
            quat_data_rev = quat_data.iloc[:, ::-1]
            print(quat_data_rev.shape)
            # print(quat_data.columns)

            # Plotting
            plt.figure()
            plt.plot(quat_data_rev, linestyle = '-', linewidth = 0.5)
            plt.xlabel('Element')
            plt.ylabel('Quaternions')
            plt.ylim([-1, 1])
            plt.title(f'Position:{ii} Visualisation for Sensor {self.sensor_list[0]}')
            plt.legend(['X', 'Y', 'Z'])














    # def PCA_analysis(self):
    #     training_dir = "Training Data/"

    #     # Training data
    #     df = make_dataframe(training_dir)
    #     df_training = df.iloc[:, :20].values
    #     # df_label = df.iloc[:, 20].values
    #     # print(df_training)

    #     # fig = plt.figure(1, figsize=(4, 3))
    #     # plt.clf()
    #     # ax = fig.add_subplot(111, projection="3d", elev=48, azim=134)
    #     # ax.set_position([0, 0, 1, 1])

    #     # y = np.choose(df_label, ["A", "B", "C", "D", "E", "F", "G", "H", "I"]).astype(float)

    #     # ax.scatter(df_training[:, 0], df_training[:, 1], df_training[:, 2], c=y, cmap=plt.cm.nipy_spectral, edgecolor="k")

    #     # plt.show()

    #     # exit()

    #     pca = PCA(n_components = 18)
    #     pca.fit(df_training)
    #     print(pca.explained_variance_ratio_)
    #     print(pca.singular_values_)