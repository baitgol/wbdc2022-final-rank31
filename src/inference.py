import os
import sys
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))#print(path)
sys.path.append(project_path)
#import ruamel_yaml as yaml
import yaml
import torch
from torch.utils.data import SequentialSampler, DataLoader
from configs.config import parse_args
from dataset.data_helper import MultiModalDataset
from utlils.category_id_map import lv2id_to_category_id
from models.model import TwoStreamModel

def inference():

    args = parse_args()
    config = yaml.load(open("configs/Finetune.yaml", 'r'), Loader=yaml.Loader)

    # args.tf_idf_model = load_train_model(args.tf_idf_file)
    # 1. load data
    dataset = MultiModalDataset(args, config, args.test_annotation, args.test_zip_frames, data_index=None, test_mode=True)
    sampler = SequentialSampler(dataset)
    dataloader = DataLoader(dataset,
                            batch_size=config["test_batch_size"],
                            sampler=sampler,
                            drop_last=False,
                            pin_memory=True,
                            num_workers=args.num_workers)

    # 2. load model
    ckpt_file = args.ckpt_file
    print(f"model_name:{ckpt_file}")
    model = TwoStreamModel(args, config)
    checkpoint = torch.load(ckpt_file, map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    if torch.cuda.is_available():
        model = model.cuda()
    model.eval()

    # 3. inference
    predictions = []
    with torch.no_grad():
        for batch in dataloader:
            # print(1)
            if torch.cuda.is_available():
                batch = {key: value.cuda() for key,value in batch.items()}
            pred_label_id = torch.argmax(model(batch, inference=True), 1)
            predictions.extend(pred_label_id.cpu().numpy())

    # 4. dump results
    with open(args.test_output_csv, 'w') as f:
        for pred_label_id, ann in zip(predictions, dataset.anns):
            video_id = ann['id']
            category_id = lv2id_to_category_id(pred_label_id)
            f.write(f'{video_id},{category_id}\n')



if __name__ == '__main__':
    inference()

