#!/usr/bin/env Rscript

# 1. Settings ====
rm(list=ls())
renv::load(project = "/home/nilomr/projects/great-tit-song")
setwd("/home/nilomr/projects/great-tit-song")
options(warn=-1)
options(readr.num_columns = 0)
# print('Making and saving plots')

# Libraries
suppressPackageStartupMessages({
  library(tidyverse)
  library(devtools)
  library(lubridate)
  library(janitor)
  library(ggrepel)
  library(RColorBrewer) #?
  library(sjPlot) #?
})


# --------------------------------------------------------------------------
# PATHS
# --------------------------------------------------------------------------

data_path <- file.path(getwd(), "resources", "brood_data")
sheet_path <- file.path(getwd(), "resources", "fieldwork", year(today()))
figures_path <- file.path(getwd(), "resources", "fieldwork", year(today()))


if (!dir.exists(data_path)) {
  dir.create(data_path, recursive = TRUE)
}

if (!dir.exists(sheet_path)) {
  dir.create(sheet_path, recursive = TRUE)
}

if (!dir.exists(figures_path)) {
  dir.create(figures_path, recursive = TRUE)
}



# 2. Nestboxes to be recorded ====

# Prepare data for plotting
newones <-
  read_csv(file.path(sheet_path, "toberecorded.csv"), 
           col_types = cols())

## This is my google key, remove before sharing
# ggmap::register_google(key = "AIzaSyDfAbhsGQ32byJTmQnpOFjQ_5yr3ViVYeI", write = TRUE)

# Centre the map here
wytham <- c(lon = -1.321898, lat = 51.771250)

# Make subtitle for plot
now <- gsub('.{3}$', '', now(tzone = "UTC"))

subtitle <- paste(
  nrow(newones),
  "new nestboxes",
  "as of",
  now,
  sep = " "
)
suppressMessages(
  gmap  <- get_googlemap(
      center = wytham,
      zoom = 14,
      scale = 4,
      maptype = "satellite",
      color = "color"
    )
)
# Make plot
new_boxes_map <-
 gmap %>%
  ggmap(base_layer = ggplot(
    aes(x = longitude, y = latitude), data = newones)) %>%
  +geom_point(colour = "white", size = 2) %>%
  +geom_text_repel(
    aes(label = Nestbox),
    direction = 'both',
    box.padding = 0.40,
    colour = "white",
    segment.alpha = 0.5,
    seed = 30
  ) %>%
  +theme_nothing() %>%
  +ggtitle("New great tit nestboxes", subtitle = subtitle) %>%
  +theme(plot.title = element_text(hjust = 0, size = 30, face = "bold")) %>%
  +theme(plot.subtitle = element_text(hjust = 0, size = 15)) %>%
  +theme(plot.margin = unit(c(1, 1, 1, 1), "cm"))

# Save plot
now <- gsub('.{3}$', '', now(tzone = "UTC"))  %>% sub(" ", "_", .)
filename <- paste0("newboxes_map_", now, ".png")

ggsave(
  new_boxes_map,
  path = figures_path,
  filename = filename,
  width = 30,
  height = 30,
  units = "cm",
  dpi = 350
)

# Make and save list

# list_path <-
#   file.path("resources",
#             "fieldwork",
#             year(today()),
#             paste0("new_", now, ".pdf"))

# newones %>% select(-x, -y) %>% 
#   knitr::kable() %>%  
#   kable_styling() %>%
#   save_kable(file = list_path)



# 3. Plot recorded vs remaining nest boxes ====


# Prepare data for plotting
recorded <-
  read_csv(file.path(sheet_path, "already-recorded.csv")) %>%
  filter(str_detect(Nestbox, "Nestbox", negate = TRUE)) %>% mutate_at(c('longitude', 'latitude'), as.numeric)

# Make subtitle for plot
now <- gsub('.{3}$', '', now(tzone = "UTC"))

subtitle <- paste(
  nrow(recorded),
  "nestboxes <b style='color:#e09200'>recorded</b> and",
  nrow(newones),
  "<b style='color:#4184b0'>to be recorded</b>",
  "as of",
  now,
  sep = " "
)

# Make plot
if (nrow(newones) > 0) {
  data = newones
} else {
  data = recorded 
}

recorded_map <-
  gmap %>%
  ggmap(base_layer = ggplot(aes(x = longitude, y = latitude), data = data)) %>%
  +geom_point(data = recorded,
              colour = "#4184b0",
              size = 2,
              alpha = 0.8) %>%
  +geom_point(
    data = newones,
    colour = "#e09200",
    size = 2,
    alpha = 0.65
  ) %>%
  +theme_void() %>%
  +theme(plot.margin = unit(c(1, 1, 1, 1), "cm")) %>%
  +labs(title = "Great Tit Song Recording Season",
        subtitle = subtitle) %>%
  +theme(
    plot.title = element_markdown(
      lineheight = 1.1,
      hjust = 0,
      size = 25,
      face = "bold"
    ),
    plot.subtitle = element_markdown(
      lineheight = 2,
      hjust = 0,
      padding = unit(c(0, 0, 8, 0), "pt"),
      size = 16
    )
  )

# Save plot
nowplot <- now %>% sub(" ", "_", .)
filename <- paste0("recorded_newboxes_map_", nowplot, ".png")

ggsave(
  recorded_map,
  path = figures_path,
  filename = filename,
  width = 30,
  height = 30,
  units = "cm",
  dpi = 350
)

print("Done!")

rm(list = ls())