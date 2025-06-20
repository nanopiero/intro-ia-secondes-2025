# -*- coding: utf-8 -*-


def show_confusion_matrix_plotly(model, val_loader, class_names, device):
    model.eval()
    preds, labels = [], []
    with torch.no_grad():
        for x, y in val_loader:
            x = x.to(device)
            outputs = model(x)
            preds.extend(outputs.argmax(1).cpu().numpy())
            labels.extend(y.numpy())

    cm = confusion_matrix(labels, preds)
    df_cm = pd.DataFrame(cm, index=class_names, columns=class_names)

    fig = px.imshow(
        df_cm,
        text_auto=True,
        color_continuous_scale='Blues',
        labels=dict(x="Predicted", y="True", color="Count"),
        title="Confusion Matrix (Validation Set)",
        width=800,
        height=800
    )
    fig.update_layout(font=dict(size=14))
    fig.show()

def get_valid_classes(train_dir, val_dir, min_count=5):
    train_classes = set(os.listdir(train_dir))
    val_classes = set(os.listdir(val_dir))
    common_classes = train_classes & val_classes
    valid_classes = []

    for cls in common_classes:
        train_cls_path = os.path.join(train_dir, cls)
        val_cls_path = os.path.join(val_dir, cls)

        if not os.path.isdir(train_cls_path) or not os.path.isdir(val_cls_path):
            continue

        train_count = len([f for f in os.listdir(train_cls_path) if os.path.isfile(os.path.join(train_cls_path, f))])
        val_count = len([f for f in os.listdir(val_cls_path) if os.path.isfile(os.path.join(val_cls_path, f))])

        if train_count >= min_count and val_count >= min_count:
            valid_classes.append(cls)

    return set(valid_classes)
def clean_directory(dir_path, valid_classes):
    for cls in os.listdir(dir_path):
        full_path = os.path.join(dir_path, cls)
        if os.path.isdir(full_path) and cls not in valid_classes:
            shutil.rmtree(full_path)


# Apply each transform in the list sequentially
def apply_transforms(img, transform_list):
    for t in transform_list:
        img = t(img)
    return img

class RandomHorizontalFlip:
    def __call__(self, img):
        if random.random() > 0.5:
            return ImageOps.mirror(img)  # left ↔ right
        return img

class RandomVerticalFlip:
    def __call__(self, img):
        if random.random() > 0.5:
            return ImageOps.flip(img)  # top ↕ bottom
        return img

class RandomDistortion:
    def __init__(self, intensity=5):
        self.intensity = intensity

    def __call__(self, img):
        w, h = img.size
        dx = self.intensity
        dy = self.intensity
        coeffs = (
            1, random.uniform(-dx/h, dx/h), 0,
            random.uniform(-dy/w, dy/w), 1, 0
        )
        return img.transform(img.size, Image.AFFINE, coeffs)

class RandomCropping:
    def __init__(self, zoommax=0.1):
        self.zoommax = zoommax

    def __call__(self, img):
        w, h = img.size
        dw = int(random.uniform(0, self.zoommax) * w)
        dh = int(random.uniform(0, self.zoommax) * h)
        left = dw
        top = dh
        right = w - dw
        bottom = h - dh
        return img.crop((left, top, right, bottom)).resize((w, h))

class Rotation:
    def __init__(self, degreemax=10):
        self.degreemax = degreemax

    def __call__(self, img):
        angle = random.uniform(-self.degreemax, self.degreemax)
        return img.rotate(angle)

class RandomColorJitter:
    def __init__(self, contrast=0.2, hue=0.1, saturation=0.2, brightness=0.2):
        self.transform = T.ColorJitter(
            contrast=contrast,
            hue=hue,
            saturation=saturation,
            brightness=brightness
        )

    def __call__(self, img):
        return self.transform(img)


def show_filters(weights, title):
    fig, axes = plt.subplots(8, 8, figsize=(10, 10))
    fig.suptitle(title, fontsize=16)
    for i, ax in enumerate(axes.flat):
        filt = weights[i, 0, :, :].cpu().numpy()  # R channel
        ax.imshow(filt, cmap='bwr', vmin=-0.2, vmax=0.2)
        ax.axis('off')
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.show()


def show_class_prediction_gallery_by_name(model, val_loader, class_names, class_name, device, max_per_col=10):
    assert class_name in class_names, f"'{class_name}' not found in class names: {class_names}"
    K = class_names.index(class_name)

    model.eval()
    all_images, all_labels, all_preds = [], [], []

    # Gather predictions and labels
    with torch.no_grad():
        for x, y in val_loader:
            x = x.to(device)
            preds = model(x).argmax(1).cpu()
            all_images.extend(x.cpu())
            all_labels.extend(y.cpu())
            all_preds.extend(preds.cpu())

    # Categorize samples
    correct, missed, false_alarm = [], [], []
    for img, label, pred in zip(all_images, all_labels, all_preds):
        if label == K and pred == K:
            correct.append((img, label, pred))
        elif label == K and pred != K:
            missed.append((img, label, pred))
        elif label != K and pred == K:
            false_alarm.append((img, label, pred))

    def sample(lst): return random.sample(lst, min(len(lst), max_per_col))
    correct_sample = sample(correct)
    missed_sample = sample(missed)
    false_alarm_sample = sample(false_alarm)

    # Plot
    fig, axes = plt.subplots(max_per_col, 3, figsize=(12, 2.5 * max_per_col))
    fig.suptitle(f'Class "{class_name}" (index {K}) — Prediction Gallery', fontsize=16)

    for i in range(max_per_col):
        for j, sample_list in enumerate([correct_sample, missed_sample, false_alarm_sample]):
            ax = axes[i, j] if max_per_col > 1 else axes[j]
            if i < len(sample_list):
                img, label, pred = sample_list[i]
                ax.imshow(np.transpose(img.numpy(), (1, 2, 0)))
                ax.set_title(f"True: {class_names[label]}\nPred: {class_names[pred]}")
            ax.axis("off")

    col_titles = ["Correct (TP)", "Missed (FN)", "False Alarm (FP)"]
    for j in range(3):
        axes[0, j].set_title(col_titles[j], fontsize=14)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()

def find_file_id(filename, drive_service):
    query = f"name='{filename}' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if not files:
        raise FileNotFoundError(f"{filename} not found in Drive.")
    return files[0]['id']