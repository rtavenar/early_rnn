import numpy as np
import os
import datetime
import pandas as pd

## EPSILON Qualitative Example


## Example
#root = "/data/EV2019/early_reward/BavarianCrops/"
root="/data/EV2019/earlyrewardalpha0.4power2/BavarianCrops/"
target = "/home/marc/projects/EV2019/images/logs/data/early_reward_p2/classes"

def split_log_in_train_test(root, target):
    os.makedirs(target, exist_ok=True)

    data = pd.read_csv(os.path.join(root,"log_earliness.csv"))
    print("writing "+os.path.join(target,"log_earliness_train.csv"))
    data.loc[data["mode"]=="train"].to_csv(os.path.join(target,"log_earliness_train.csv"))
    print("writing "+os.path.join(target,"log_earliness_test.csv"))
    data.loc[data["mode"]=="test"].to_csv(os.path.join(target,"log_earliness_test.csv"))

# qualitative example
split_log_in_train_test(root, target)

for run in [0,1,2]:
    # epsilon examples
    split_log_in_train_test("/data/EV2019/earlyreward-alpha0.4-epsilon0-run{}/BavarianCrops".format(run), "/home/marc/projects/EV2019/images/logs/data/epsilon0_r{}".format(run))
    split_log_in_train_test("/data/EV2019/earlyreward-alpha0.4-epsilon1-run{}/BavarianCrops".format(run), "/home/marc/projects/EV2019/images/logs/data/epsilon1_r{}".format(run))
    split_log_in_train_test("/data/EV2019/earlyreward-alpha0.4-epsilon10-run{}/BavarianCrops".format(run), "/home/marc/projects/EV2019/images/logs/data/epsilon10_r{}".format(run))


os.makedirs(target,exist_ok=True)

arraypath = os.path.join(root,"npy")
arrays = os.listdir(arraypath)

file = "{array}_{epoch}.npy"
os.path.exists(os.path.join(arraypath,file.format(array="t_stops", epoch=1)))

# sequencelength 70 observations from January to December
TMAX = 70

def load_class_tstop(epoch):

    t_stops = (np.load(os.path.join(arraypath,file.format(array="t_stops", epoch=epoch)))+1) / TMAX
    labels = np.load(os.path.join(arraypath,file.format(array="labels", epoch=epoch)))

    grouped = [t_stops[labels == i] for i in np.unique(labels)]
    return grouped

grouped = load_class_tstop(100)
classnames = ["meadows","winter barley","corn","winter wheat","summer barley","clover","winter triticale"]


# produce csv file for boxplots of the format:
#index median box_top box_bottom whisker_top whisker_bottom
# https://towardsdatascience.com/understanding-boxplots-5e2df7bcbd51
boxplot=r"""
median={median},
upper quartile={upperquartile},
lower quartile={lowerquartile},
upper whisker={upperwhisker},
lower whisker={lowerwhisker},
"""

txt = os.path.join(target, "stops.csv")
print("writing " + txt)
df = pd.DataFrame(grouped).T
df.columns = classnames

for classname in classnames:
    filename=os.path.join(target, classname.replace(" ","_")+".csv")
    print("writing "+filename)
    pd.DataFrame(df[classname]).to_csv(filename)
#df.to_csv(txt)

print()
print("Boxplots metrics")
print()
for cl in range(len(grouped)):

    data = grouped[cl]
    median = np.median(data)
    Q3 = np.percentile(data, 75)
    Q1 = np.percentile(data, 25)
    IQR = Q3-Q1
    max = Q3 + 1.5 * IQR
    min = Q1 - 1.5 * IQR


    print(classnames[cl])
    print(boxplot.format(
        median=median,
        upperquartile=Q1,
        lowerquartile=Q3,
        upperwhisker=max,
        lowerwhisker=min))

    #print(cl, median, Q3, Q1, max, min, classnames[cl], sep=",")

print()

pass
means = list()
medians = list()
stds = list()

for epoch in range(1,100):
    grouped = load_class_tstop(epoch)
    means.append([epoch] + [stop.mean() for stop in grouped])
    medians.append([epoch] + [np.median(stop) for stop in grouped])
    stds.append([epoch] + [np.std(stop) for stop in grouped])

import pandas as pd
means = pd.DataFrame(means, columns=["epoch"]+classnames).set_index("epoch")
medians = pd.DataFrame(medians, columns=["epoch"]+classnames).set_index("epoch")
stds = pd.DataFrame(stds, columns=["epoch"]+classnames).set_index("epoch")

print("writing "+os.path.join(target,"mean.csv"))
means.to_csv(os.path.join(target,"mean.csv"))
medians.to_csv(os.path.join(target,"median.csv"))
stds.to_csv(os.path.join(target,"stds.csv"))
(means - stds).to_csv(os.path.join(target,"mean-std.csv"))
(means + stds).to_csv(os.path.join(target,"mean+std.csv"))

last_mean = np.array(means)[-1,:]
last_std = np.array(stds)[-1,:]

def ratio2date(ratio):
    return datetime.datetime(year=2018, month=1, day=1) + datetime.timedelta(days=ratio * 365)

dates = [ratio2date(mean).strftime(r"%b$^{\nth{%d}}$") for mean in last_mean]
std_days = (last_std*365).astype(int)

print("class & stopping date")
for i in range(len(dates)):
    print(r"{} & {} $\pm$ {} days \\".format(classnames[i], dates[i], std_days[i]))
pass

import matplotlib.pyplot as plt
import seaborn as sns

fix, axs = plt.subplots(7,1, figsize=(12,12))

for i in range(7):
    hist = np.histogram(grouped[i], bins=69, density=True)[0]
    #hist /= hist.sum()
    axs[i].bar(np.arange(len(hist)), hist)
    #sns.distplot(grouped[i], kde=False, rug=False, ax=ax, bins=70);
plt.show()

#pd.DataFrame(data, columns=["epoch","mean","median","std"])
#data.append(dict(
#    epoch=epoch,
#    mean=mean,
#    median=median,
#    std=std
#))

import matplotlib.pyplot as plt

confusion_matrix = np.load("/data/EV2019/earlyrewardalpha0.4power2/BavarianCrops/npy/confusion_matrix_99.npy")
plt.imshow(confusion_matrix)

confusion_matrix = confusion_matrix.astype(float)

total = np.sum(confusion_matrix)
n_classes, _ = confusion_matrix.shape
classes = []
overall_accuracy = np.sum(np.diag(confusion_matrix)) / total

# calculate Cohen Kappa (https://en.wikipedia.org/wiki/Cohen%27s_kappa)
N = total
p0 = np.sum(np.diag(confusion_matrix)) / N
pc = np.sum(np.sum(confusion_matrix, axis=0) * np.sum(confusion_matrix, axis=1)) / N ** 2
kappa = (p0 - pc) / (1 - pc)

recall = np.diag(confusion_matrix) / (np.sum(confusion_matrix, axis=1) + 1e-12)
precision = np.diag(confusion_matrix) / (np.sum(confusion_matrix, axis=0) + 1e-12)
f1 = (2 * precision * recall) / ((precision + recall) + 1e-12)

# Per class accuracy
cl_acc = np.diag(confusion_matrix) / (confusion_matrix.sum(1) + 1e-12)

for cl in range(len(classnames)):
    print("{}:{:.2f}".format(classnames[cl], cl_acc[cl]))

pass