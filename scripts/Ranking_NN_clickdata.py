import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from sklearn.metrics import ndcg_score

class Net(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(input_dim, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, output_dim)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

class MyDataset(Dataset):
    def __init__(self, data):
        self.x = torch.Tensor(data.drop(['target'], axis=1).values)
        self.y = torch.Tensor(data['target'].values.reshape(-1, 1))

    def __len__(self):
        return len(self.x)

    def __getitem__(self, idx):
        return self.x[idx], self.y[idx]

data_ = pd.read_csv('ru_click_wiki2vec.tsv', sep="\t")
testset=pd.read_pickle("ru_click_wiki2vec_testset.tsv", sep="\t")
test_queries=list(testset["wikidata_id"].unique())
## removing testset entities from training data
data_=data_.loc[~data_["wikidata_id"].isin(test_queries),]
data_=data_.rename(columns={"target_sum":"target"})

#data_=data_.loc[data_["target"].notna(),]
#data_=data_.loc[data_["vector"].notna(),]
del data_["entity"]
del data_["wikidata_id"]
data1=data_["vector"].apply(pd.Series)
data=pd.concat((data_[["target"]], data1), axis=1)

testset=testset.rename(columns={"target_sum":"target"})
testset1=testset["vector"].apply(pd.Series)
test_data=pd.concat((testset[["target"]], testset1), axis=1)
#data=data.dropna()
train_data = data


# Create data loaders for training and test data
trainloader = DataLoader(MyDataset(train_data), batch_size=32, shuffle=True)
testloader = DataLoader(MyDataset(test_data), batch_size=32, shuffle=False)

net = Net(input_dim=len(data.columns) - 1, output_dim=1)
optimizer = optim.Adam(net.parameters(), lr=0.001)

criterion = nn.MSELoss()

for epoch in range(100):
    running_loss = 0.0
    for i, data in enumerate(trainloader, 0):
        inputs, targets = data
        optimizer.zero_grad()
        outputs = net(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
    print('Epoch %d loss: %.3f' % (epoch + 1, running_loss / len(trainloader)))

total_loss = 0.0
net.eval()

#### Predictions on the testset
with torch.no_grad():
    predictions=[]
    for inputs, targets in testloader:
        batch_predictions=net(inputs)
        predictions.append(batch_predictions)

#torch.save(net.state_dict(), "ru_click_nn_model.pth")
predictions=torch.cat(predictions)
testset["prediction"]=predictions.numpy()
testset=testset[["entity", "answer_topic","score", "target", "prediction"]]

df1=testset.groupby("answer_topic")["score"].apply(list).reset_index(name="ground")
df2=testset.groupby("answer_topic")["prediction"].apply(list).reset_index(name="prediction")
evaluation_mrg=pd.merge(left=df1, right=df2, how="inner", on=["answer_topic"])

evaluation_mrg["ground_"]=evaluation_mrg.apply(lambda row: [], axis=1)
evaluation_mrg["prediction_"]=evaluation_mrg.apply(lambda row: [], axis=1)

evaluation_mrg["f"]=evaluation_mrg.apply(lambda row: row.ground_.append(row.ground), axis=1)
evaluation_mrg["g"]=evaluation_mrg.apply(lambda row: row.prediction_.append(row.prediction), axis=1)
evaluation_mrg["len"]=evaluation_mrg.apply(lambda row: len(row.prediction), axis=1)
#evaluation_mrg=evaluation_mrg1.loc[evaluation_mrg["len"]>1,]
evaluation_mrg["ndcg"]=evaluation_mrg.apply(lambda row: ndcg_score(row.ground_, row.prediction_), axis=1)
evaluation_mrg=evaluation_mrg[["answer_topic","ground","prediction","ndcg"]]
print(evaluation_mrg)
#evaluation_mrg.to_pickle("ru_click_nn_results")
print("*************ndcg is: ", np.mean(evaluation_mrg["ndcg"]))


