import dotClassify
import matplotlib.pyplot as plt

if __name__ == '__main__':
    a = dotClassify.classify([1])
    # a.PCA_analysis()
    # a.make_model("all")
    # a.test_model()
    # a.display_confusion_matrix()
    # a.display_data_3D_plot()
    a.visualise_data()

    # Display plots
    plt.show()