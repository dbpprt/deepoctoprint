var express = require('express');
var bodyParser = require('body-parser');
var multer = require('multer')
var path = require('path');
var fs = require('fs');
const rateLimit = require("express-rate-limit");
var AWS = require('aws-sdk');

const uploadFolder = './uploads';

const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 20 // limit each IP to 100 requests per windowMs
});

const s3 = new AWS.S3({
    accessKeyId: 'minio',
    secretAccessKey: 'minio123',
    endpoint: 'http://127.0.0.1:9000',
    s3ForcePathStyle: true,
    signatureVersion: 'v4'
});

const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, uploadFolder);
    },
    filename: function (req, file, cb) {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        
        const installationKey = req.header('x-installation-key');
        const printId = req.header('x-print-id');
        const startTime = req.header('x-start-time');
        const time = req.header('x-time');
        const currentEvent = req.header('x-current-event');

        cb(null, installationKey + '_' + printId + '_' + startTime + '-' + time + '-' + currentEvent + '-' + uniqueSuffix + '.jpg');
    }
});

var app = express();
var upload = multer({ storage: storage });

app.set('trust proxy', 1);
app.use(limiter);

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(express.static(path.join(__dirname, 'public')));

// https://stackoverflow.com/questions/27670051/upload-entire-directory-tree-to-s3-using-aws-sdk-in-node-js
// pretty ugly - no await but works
function uploadArtifactsToS3() {
    const walkSync = (currentDirPath, callback) => {
        fs.readdirSync(currentDirPath).forEach((name) => {
            const filePath = path.join(currentDirPath, name);
            const stat = fs.statSync(filePath);
            if (stat.isFile()) {
                callback(filePath, stat);
            } else if (stat.isDirectory()) {
                walkSync(filePath, callback);
            }
        });
    };

    walkSync(uploadFolder, async (filePath) => {
        let bucketPath = filePath.substring(uploadFolder.length - 1);
        let params = {
            Bucket: process.env.SOURCE_BUCKET || 'bucket',
            Key: `${bucketPath}`,
            Body: fs.readFileSync(filePath)
        };
        try {
            await s3.putObject(params).promise();
            console.log(`Successfully uploaded ${bucketPath} to s3 bucket`);
            await fs.promises.unlink(filePath);
        } catch (error) {
            console.error(`error in uploading ${bucketPath} to s3 bucket`);
            throw new Error(`error in uploading ${bucketPath} to s3 bucket`);
        }
    });
}

app.post('/v1/upload', upload.array('pic'), function (req, res, next) {
    res.sendStatus(200);
});

app.listen(8776, function () {
    console.log('running....');

    setInterval(uploadArtifactsToS3, 60000);
    uploadArtifactsToS3();
});